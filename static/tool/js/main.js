/**
 * tool/assets/js/main.js - Phiên bản Fix lỗi AI & Giao diện
 */

let datasetId = null;
let currentCols = [];
let selectedMultiCols = new Set();
let lastUsedCols = [];
let tempChartType = null;
let currentMultiModal = null;
let currentCleanModal = null;
let showPct = false;
let lastStatsType = null;
let lastStatsData = null;

// Hàm lấy Element an toàn (tránh lỗi null)
const getEl = (id) => document.getElementById(id);

const els = {
    fileInput: getEl('datasetFile'),
    uploadText: getEl('uploadText'),
    fileStatus: getEl('fileStatus'),
    colDisplay: getEl('colDisplay'),
    plotArea: getEl('plotArea'),
    chatBox: getEl('chatBox'),
    messages: getEl('messages'),
    chatInput: getEl('chatInput'),
    supportFab: getEl('supportFab'),
    multiModal: getEl('multiModal'),
    cleanModal: getEl('cleanModal'),
    colSearchInput: getEl('colSearchInput'),
    btnConfirmText: getEl('btnConfirmText'),
    availableList: getEl('availableList'),
    selectedList: getEl('selectedList'),
    selectedCountDisplay: getEl('selectedCountDisplay')
};

// --- EVENTS ---
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll(".accordion-header").forEach(header => {
        header.onclick = (e) => {
            e.preventDefault();
            header.parentElement.classList.toggle("active");
        };
    });
});

window.onclick = function (event) {
    if (event.target == els.multiModal) els.multiModal.style.display = "none";
    if (event.target == els.cleanModal) els.cleanModal.style.display = "none";
};

if (els.chatInput) {
    els.chatInput.addEventListener("keypress", (e) => { if (e.key === "Enter") { e.preventDefault(); sendChat(); } });
}

// Xử lý nút gạt phần trăm
document.addEventListener('change', function (e) {
    if (e.target && e.target.id === 'showPctToggle') {
        showPct = e.target.checked;
        if (datasetId && lastUsedCols && lastUsedCols.length > 0) {
            // Vẽ lại biểu đồ hiện tại với chế độ mới
            const activeChartType = window.tempChartType || 'column';
            // Nếu đang ở trong modal chọn cột thì không vẽ ngay, 
            // chỉ vẽ khi đã có dữ liệu và loại biểu đồ được xác định
            if (activeChartType !== 'selection') {
                drawPlot(activeChartType, lastUsedCols);
            }
        }
    }
});

function toggleChat() {
    if (els.chatBox) {
        els.chatBox.classList.toggle('open');
        if (els.supportFab) els.supportFab.style.display = els.chatBox.classList.contains('open') ? 'none' : 'flex';
    }
}

function sendPrompt(text) {
    const input = document.getElementById('chatInput');
    input.value = text;
    sendChat();
}

// --- UPLOAD ---
if (els.fileInput) {
    els.fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const fd = new FormData(); fd.append('file', file);
        try {
            els.uploadText.innerText = "Đang tải lên...";
            els.fileStatus.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang xử lý...`;
            const res = await fetch('/api/upload', { method: 'POST', body: fd });
            const data = await res.json();
            if (data.error) throw new Error(data.error);

            datasetId = data.dataset_id;
            currentCols = data.columns || [];
            lastRowCount = data.row_count || 0;
            lastColCount = data.col_count || 0;
            selectedMultiCols.clear(); lastUsedCols = [];

            if (els.colDisplay) {
                els.colDisplay.innerText = "Chưa chọn cột nào";
                els.colDisplay.style.color = "#9ca3af";
            }

            els.fileStatus.innerHTML = `<i class="fa-solid fa-file-excel"></i> <strong>${data.original_filename}</strong>`;
            els.uploadText.innerText = "Đổi file khác";

            if (confirm("Tải thành công! Có muốn làm sạch dữ liệu không?")) openCleanModal();
        } catch (err) {
            alert("Lỗi: " + err.message);
            els.uploadText.innerText = "Tải file Excel";
            els.fileStatus.innerText = "Lỗi tải file";
        }
    };
}

// --- DUAL LIST MODAL ---
function openMultiModal(type) {
    if (!datasetId) return alert("Vui lòng tải file trước!");
    tempChartType = type;

    const config = {
        'selection': { title: 'Chọn dữ liệu', btn: 'Lưu lựa chọn' },
        'grouped': { title: 'Cột Ghép nhóm – chọn nhiều cột', btn: 'Vẽ ngay' },
        'stacked': { title: 'Cột Chồng Dọc – chọn nhiều cột', btn: 'Vẽ ngay' },
        'stacked_h': { title: 'Cột Chồng Ngang – chọn nhiều cột', btn: 'Vẽ ngay' },
        'reliability': { title: 'Độ tin cậy Cronbach\'s Alpha (Chọn các mục)', btn: 'Tính toán' },
        'correlation': { title: 'Tương quan Pearson (Chọn các cột)', btn: 'Tính toán' },
        'regression': { title: 'Hồi quy (Cột 1: Biến phụ thuộc, còn lại: Độc lập)', btn: 'Chạy hồi quy' },
    };
    const cfg = config[type] || config['selection'];
    document.getElementById('multiTitle').innerText = cfg.title;
    document.getElementById('btnConfirmText').innerText = cfg.btn;

    if (els.colSearchInput) els.colSearchInput.value = "";
    renderDualList();

    // Tạo instance và hiển thị modal
    const modalEl = document.getElementById('multiModal');
    currentMultiModal = new bootstrap.Modal(modalEl);
    currentMultiModal.show();
}

function renderDualList() {
    const searchVal = els.colSearchInput ? els.colSearchInput.value.toLowerCase() : "";
    if (els.availableList) els.availableList.innerHTML = '';
    if (els.selectedList) els.selectedList.innerHTML = '';

    selectedMultiCols.forEach(col => {
        const div = document.createElement('div');
        div.className = 'dual-item target';
        div.innerHTML = `<span>${col}</span><i class="fa-solid fa-xmark remove-icon"></i>`;
        div.onclick = () => { selectedMultiCols.delete(col); renderDualList(); };
        if (els.selectedList) els.selectedList.appendChild(div);
    });

    currentCols.forEach(col => {
        if (selectedMultiCols.has(col)) return;
        if (searchVal && !col.toLowerCase().includes(searchVal)) return;
        const div = document.createElement('div');
        div.className = 'dual-item source';
        div.innerHTML = `<span>${col}</span>`;
        div.onclick = () => { selectedMultiCols.add(col); renderDualList(); };
        if (els.availableList) els.availableList.appendChild(div);
    });
    if (els.selectedCountDisplay) els.selectedCountDisplay.innerText = selectedMultiCols.size;
}

if (els.colSearchInput) els.colSearchInput.oninput = () => renderDualList();
function clearAllSelection() { selectedMultiCols.clear(); renderDualList(); }

function applyMulti() {
    const arr = Array.from(selectedMultiCols);
    // Đọc từ cả window.tempChartType (set bởi override trong HTML) lẫn biến let
    const chartType = window.tempChartType || tempChartType;
    const multiColTypes = ['grouped', 'stacked', 'stacked_h'];
    if (arr.length < 1) return alert("Chọn ít nhất 1 cột!");
    if (multiColTypes.includes(chartType) && arr.length < 2)
        return alert("Biểu đồ so sánh cần chọn ít nhất 2 cột!");
        
    // Chặn biểu đồ đơn khi chọn nhiều cột
    const singleColTypes = ['pie', 'donut'];
    if (singleColTypes.includes(chartType) && arr.length > 1) {
        alert("⚠️ Biểu đồ Tròn và Donut chỉ hỗ trợ 1 biến. Hệ thống sẽ tự động chuyển sang Biểu đồ Cột để so sánh.");
        window.tempChartType = 'column'; // Reset lại loại biểu đồ
    }
    
    lastUsedCols = arr;

    if (els.colDisplay) {
        els.colDisplay.style.color = "#1d4ed8";
        els.colDisplay.innerText = arr.length === 1 ? arr[0] : `${arr[0]} (+${arr.length - 1} cột)`;
    }

    // Đóng modal bằng Bootstrap API (dùng getInstance để luôn lấy đúng instance)
    const modalEl = document.getElementById('multiModal');
    const modal = bootstrap.Modal.getInstance(modalEl) || currentMultiModal || window.currentMultiModal;
    if (modal) { modal.hide(); }
    window.currentMultiModal = null;
    currentMultiModal = null;

    if (chartType && chartType !== 'selection') {
        const statsTypes = ['reliability', 'correlation', 'regression'];
        if (statsTypes.includes(chartType)) {
            runStatistics(chartType, arr);
        } else {
            drawPlot(chartType, arr);
        }
    }
}

// --- VẼ BIỂU ĐỒ ---
async function setType(type) {
    if (!datasetId) return alert("Chưa có file!");
    if (!lastUsedCols || lastUsedCols.length === 0) {
        if (confirm("Chưa chọn dữ liệu. Mở danh sách chọn?")) openMultiModal('selection');
        return;
    }
    drawPlot(type, lastUsedCols);
}

async function drawPlot(type, cols) {
    if (!cols || cols.length === 0) return;

    // Biểu đồ cần nhiều cột để so sánh
    const multiColTypes = ['grouped', 'stacked', 'stacked_h'];

    let plots = [];
    if (multiColTypes.includes(type)) {
        // grouped/stacked: dùng tất cả cột được chọn
        plots = [{ type, cols }];
    } else {
        // Biểu đồ đơn: nếu chọn nhiều cột vẽ từng cột riêng, hoặc gom lại
        if (cols.length === 1) {
            plots = [{ type, cols }];
        } else {
            // Với pie/donut chỉ dùng cột đầu, các loại khác gom nhiều cột
            if (type === 'pie' || type === 'donut') {
                plots = [{ type, cols: [cols[0]] }];
            } else {
                plots = [{ type, cols }];
            }
        }
    }

    document.getElementById('plotArea').innerHTML = `
    <div class="d-flex flex-column align-items-center justify-content-center gap-2" style="min-height:300px;">
      <div class="spinner-border text-primary" role="status"></div>
      <span class="text-muted small">Đang vẽ biểu đồ...</span>
    </div>`;

    try {
        const res = await fetch('/api/plot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dataset_id: datasetId,
                plots: plots.map(p => ({ ...p, show_pct: showPct }))
            })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        if (data.images && data.images.length) {
            document.getElementById('plotArea').innerHTML =
                `<img src="${data.images[0]}" class="fade-in" style="max-width:100%;height:auto;">`;
            if (document.getElementById('autoAnalyze')?.checked) {
                if (document.getElementById('chatBox')?.classList.contains('d-none')) toggleChat();
                sendPrompt(`Phân tích tóm tắt cho dữ liệu: ${cols.slice(0, 3).join(', ')}${cols.length > 3 ? '...' : ''}`);
            }
        } else {
            document.getElementById('plotArea').innerHTML =
                '<div class="text-center text-muted p-4"><i class="fa-solid fa-circle-exclamation fs-3 mb-2 d-block text-warning"></i>Không thể vẽ biểu đồ với dữ liệu này.</div>';
        }
    } catch (e) {
        document.getElementById('plotArea').innerHTML =
            `<div class="text-center text-danger p-4"><i class="fa-solid fa-triangle-exclamation fs-3 mb-2 d-block"></i>Lỗi: ${e.message}</div>`;
    }
}

// --- CHAT & UTILS ---
async function sendChat() {
    const input = document.getElementById('chatInput');
    const txt = input.value.trim();
    if (!txt) return;
    addMsg(txt, 'user');
    input.value = '';

    const modelEl = document.getElementById('engineModel');
    const modelVal = modelEl ? modelEl.value : "llama-3.3-70b-versatile";

    const botId = addMsg('<div class="loader" style="width:15px;height:15px;border-width:2px"></div>', 'bot');

    try {
        const res = await fetch('/api/assistant', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: txt,
                dataset_id: datasetId,
                cols: lastUsedCols,
                selected_col: lastUsedCols[0],
                model: modelVal
            })
        });
        const data = await res.json();
        const botMsg = document.getElementById(botId);
        if (botMsg) {
            botMsg.innerHTML = data.reply.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br>');
            if (data.suggestions && data.suggestions.length) {
                const chipsContainer = document.querySelector('.suggestion-chips');
                if (chipsContainer) {
                    chipsContainer.innerHTML = '';
                    data.suggestions.forEach(s => {
                        const chip = document.createElement('span');
                        chip.textContent = s;
                        chip.onclick = () => sendPrompt(s);
                        chipsContainer.appendChild(chip);
                    });
                }
            }
        }
    } catch (e) {
        const botMsg = document.getElementById(botId);
        if (botMsg) botMsg.innerHTML = `<span style='color:red'>Lỗi hệ thống: ${e.message}</span>`;
    }
}

function addMsg(txt, role) {
    const id = 'msg-' + Date.now();
    if (els.messages) {
        els.messages.innerHTML += `<div class="message ${role}"><div class="bubble" id="${id}">${txt}</div></div>`;
        els.messages.scrollTop = els.messages.scrollHeight;
    }
    return id;
}

function openCleanModal() {
    if (!datasetId) return alert("Vui lòng tải file trước!");
    const modalEl = document.getElementById('cleanModal');
    currentCleanModal = new bootstrap.Modal(modalEl);
    currentCleanModal.show();
}
function closeModal(modalId) {
    const modalEl = document.getElementById(modalId);
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
    }
}

async function runClean() {
    try {
        const btn = document.querySelector('#cleanModal .btn-primary');
        if (btn) {
            btn.innerText = "Đang xử lý...";
            btn.disabled = true;
        }

        const res = await fetch('/api/clean', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dataset_id: datasetId,
                drop_na: document.getElementById('chkNa')?.checked,
                drop_duplicates: document.getElementById('chkDup')?.checked
            })
        });
        const d = await res.json();
        if (d.error) throw new Error(d.error);

        // Đóng modal ngay sau khi thành công
        const cleanModalEl = document.getElementById('cleanModal');
        const cleanModal = bootstrap.Modal.getInstance(cleanModalEl) || window.currentCleanModal;
        if (cleanModal) { cleanModal.hide(); }
        window.currentCleanModal = null;

        // Cập nhật kết quả vào bảng trong modal (nếu còn visible) và hiển thị toast
        const resultBox = document.getElementById('cleanResult');
        if (resultBox) {
            const oldRowsEl = document.getElementById('cleanOldRows');
            const oldColsEl = document.getElementById('cleanOldCols');
            const newRowsEl = document.getElementById('cleanNewRows');
            const newColsEl = document.getElementById('cleanNewCols');
            const diffRowsEl = document.getElementById('cleanDiffRows');
            if (oldRowsEl) oldRowsEl.innerText = d.old_shape[0];
            if (oldColsEl) oldColsEl.innerText = d.old_shape[1];
            if (newRowsEl) newRowsEl.innerText = d.new_shape[0];
            if (newColsEl) newColsEl.innerText = d.new_shape[1];
            if (diffRowsEl) diffRowsEl.innerText = d.old_shape[0] - d.new_shape[0];
        }
        showCleanToast(d.old_shape[0], d.new_shape[0]);
    } catch (e) {
        alert("Lỗi: " + e.message);
    } finally {
        const btn = document.getElementById('btnRunClean');
        if (btn) { btn.innerText = 'Thực hiện ngay'; btn.disabled = false; }
    }
}

function showCleanToast(oldRows, newRows) {
    const removed = oldRows - newRows;
    let toastEl = document.getElementById('cleanToast');
    if (!toastEl) return; // fallback
    document.getElementById('cleanToastBody').innerHTML =
        `<i class="fa-solid fa-circle-check text-success me-2"></i>
        <strong>Làm sạch thành công!</strong><br>
        <span class="small">Trước: <b>${oldRows}</b> dòng &nbsp;→&nbsp; Sau: <b>${newRows}</b> dòng &nbsp;
        <span class="badge bg-warning text-dark">Đã xóa ${removed} dòng</span></span>`;
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
}

function downloadImage() {
    const img = els.plotArea ? els.plotArea.querySelector('img') : null;
    if (img) { const a = document.createElement('a'); a.href = img.src; a.download = 'chart.png'; a.click(); }
    else alert("Chưa có biểu đồ!");
}

let lastRowCount = 0;
let lastColCount = 0;

async function exportReport() {
    const img = els.plotArea ? els.plotArea.querySelector('img') : null;
    if (!img && !lastStatsData) return alert("Vui lòng vẽ biểu đồ hoặc chạy thống kê SPSS trước khi xuất báo cáo!");

    const btn = document.querySelector('.top-actions .btn-primary') || document.querySelector('button[onclick="exportReport()"]');
    const oldHtml = btn ? btn.innerHTML : "";
    if (btn) { btn.innerHTML = '<i class="fa-solid fa-brain fa-fade me-1"></i> AI đang phân tích đa tầng...'; btn.disabled = true; }

    try {
        let analysis2 = "Chưa có nhận xét mô tả.";
        let analysis3 = "Phương pháp thống kê chuẩn tắc.";
        let analysis4 = "Chưa có phân tích chi tiết.";
        let analysis5 = "Chưa có kết luận cụ thể.";
        
        // TỰ ĐỘNG: Tạo nhận xét đa tầng từ AI
        const statsSummary = lastStatsData ? JSON.stringify(lastStatsData) : "Thống kê mô tả tổng quát";
        const prompt = `Hãy viết báo cáo NCKH chuyên nghiệp và CỰC KỲ CHI TIẾT cho dữ liệu sau: ${statsSummary}.
        Danh sách các biến phân tích: ${lastUsedCols.join(', ')}.
        
        Yêu cầu trả về cấu trúc sau, mỗi phần viết ít nhất 3-5 đoạn văn dài (không thêm lời dẫn):
        [MÔ TẢ CHI TIẾT]: (Viết nhận xét cực kỳ sâu cho từng biến số: ${lastUsedCols.join(', ')}. Phân tích ý nghĩa của các con số cao/thấp nhất)
        [PHƯƠNG PHÁP]: (Mô tả chi tiết phương pháp luận, cỡ mẫu, cách thu thập và làm sạch dữ liệu)
        [CHUYÊN SÂU]: (Biện luận khoa học, so sánh các biến, phân tích nguyên nhân và các yếu tố ảnh hưởng)
        [KÌ VỌNG & KẾT LUẬN]: (Viết ít nhất 500 từ về Kết luận, Kiến nghị thực tiễn cho Khoa/Trường, và hướng phát triển đề tài)
         Văn phong học thuật cao cấp, chuyên nghiệp.`;

        try {
            const aiRes = await fetch('/api/assistant', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: prompt,
                    dataset_id: datasetId,
                    cols: lastUsedCols,
                    model: "llama-3.3-70b-versatile"
                })
            });
            const aiData = await aiRes.json();
            if (aiData.reply) {
                const fullText = aiData.reply.split('///')[0];
                analysis2 = fullText.split('[PHƯƠNG PHÁP]')[0].replace('[MÔ TẢ CHI TIẾT]:','').trim();
                const part345 = fullText.split('[PHƯƠNG PHÁP]')[1] || "";
                analysis3 = part345.split('[CHUYÊN SÂU]')[0].trim();
                const part45 = part345.split('[CHUYÊN SÂU]')[1] || "";
                analysis4 = part45.split('[KÌ VỌNG & KẾT LUẬN]')[0].trim();
                analysis5 = part45.split('[KÌ VỌNG & KẾT LUẬN]')[1] || "Báo cáo xác nhận tính khoa học của bộ dữ liệu.";
            }
        } catch (aiErr) {
            console.error("AI Multi-Stage Analysis Error:", aiErr);
        }

        // KẾT XUẤT WORD
        if (btn) btn.innerHTML = '<i class="fa-solid fa-file-word fa-bounce me-1"></i> Đang hoàn thiện báo cáo...';
        
        const res = await fetch('/api/generate_doc', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image: img ? img.src : null,
                col_name: lastUsedCols.join(', '),
                dataset_id: datasetId,
                total_rows: lastRowCount,
                total_cols: lastColCount,
                analysis_ii: analysis2,
                analysis_meth: analysis3,
                analysis_iv: analysis4,
                analysis_v: analysis5,
                stats_type: lastStatsType,
                stats_data: lastStatsData
            })
        });

        if (!res.ok) throw new Error("Lỗi kết nối máy chủ tạo file Word.");

        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(blob);
        a.download = `Bao_cao_HOU_Professional_Full_${Date.now()}.docx`;
        a.click();
    } catch (e) {
        alert("Lỗi xuất báo cáo: " + e.message);
    } finally {
        if (btn) { btn.innerHTML = oldHtml; btn.disabled = false; }
    }
}

// --- SPSS STATISTICS ---
async function runStatistics(type, cols) {
    const plotArea = document.getElementById('plotArea');
    plotArea.innerHTML = `<div class="p-5 text-center"><div class="spinner-border text-primary"></div><p class="mt-2 small">Đang chạy thuật toán thống kê...</p></div>`;

    try {
        let endpoint = `/api/analysis/${type}`;
        let body = { dataset_id: datasetId, cols: cols };
        if (type === 'regression') {
            body = { dataset_id: datasetId, target: cols[0], predictors: cols.slice(1) };
        }

        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        lastStatsType = type;
        lastStatsData = data;
        renderStatsResult(type, data);
    } catch (e) {
        plotArea.innerHTML = `<div class="alert alert-danger m-3">${e.message}</div>`;
    }
}

function renderStatsResult(type, data) {
    const plotArea = document.getElementById('plotArea');
    let html = `<div class="stats-result p-4 w-100 overflow-auto animate__animated animate__fadeIn">`;

    if (type === 'reliability') {
        html += `<h5 class="fw-bold text-primary mb-3">KẾT QUẢ ĐỘ TIN CẬY (CRONBACH'S ALPHA)</h5>
        <div class="row mb-4"><div class="col-md-6"><div class="card p-3 border-0 bg-white shadow-sm">
            <div class="small text-muted">Hệ số Cronbach's Alpha:</div>
            <div class="display-5 fw-bold text-success">${data.alpha}</div>
            <div class="badge bg-success mt-2">Mức độ: ${data.status}</div>
        </div></div>
        <div class="col-md-6"><ul class="list-group list-group-flush small">
            <li class="list-group-item d-flex justify-content-between"><span>Số cột quan sát:</span><b>${data.item_count}</b></li>
            <li class="list-group-item d-flex justify-content-between"><span>Số mẫu (N):</span><b>${data.sample_size}</b></li>
        </ul></div></div>`;
    } else if (type === 'correlation') {
        html += `<h5 class="fw-bold text-primary mb-3">MA TRẬN TƯƠNG QUAN PEARSON</h5>
        <table class="table table-sm table-bordered small bg-white">
            <thead class="table-light"><tr><th>Cột</th>${data.columns.map(c => `<th class="text-center">${c.substring(0, 10)}...</th>`).join('')}</tr></thead>
            <tbody>${data.matrix.map(row => `<tr><td class="fw-bold">${row.column}</td>${data.columns.map(c => `<td class="text-center ${row[c] >= 0.5 ? 'bg-info-subtle fw-bold' : ''}">${row[c]}</td>`).join('')}</tr>`).join('')}</tbody>
        </table>`;
    } else if (type === 'regression') {
        html += `<h5 class="fw-bold text-primary mb-3">TÓM TẮT MÔ HÌNH HỒI QUY</h5>
        <div class="row g-2 mb-3">
            <div class="col-6 col-md-3"><div class="p-2 border rounded bg-white small text-center">R-Squared: <b>${data.r_squared}</b></div></div>
            <div class="col-6 col-md-3"><div class="p-2 border rounded bg-white small text-center">Adj R-Squared: <b>${data.adj_r_squared}</b></div></div>
            <div class="col-6 col-md-3"><div class="p-2 border rounded bg-white small text-center">F-Sig: <b>${data.f_pvalue}</b></div></div>
        </div>
        <table class="table table-sm table-striped small bg-white">
            <thead class="table-dark"><tr><th>Biến</th><th>Hệ số B</th><th>Std.Error</th><th>P-value</th><th>Sig</th></tr></thead>
            <tbody>${data.coefficients.map(c => `<tr><td class="fw-bold">${c.variable}</td><td>${c.coefficient}</td><td>${c.std_err}</td><td>${c.p_value}</td><td class="text-danger fw-bold">${c.sig}</td></tr>`).join('')}</tbody>
        </table>`;
    }

    html += `</div>`;
    plotArea.innerHTML = html;
}

// --- POWER BI CONNECT ---
async function connectPowerBI() {
    if (!datasetId) return alert("Chưa có file dữ liệu!");
    try {
        const res = await fetch('/api/powerbi/generate_info', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset_id: datasetId })
        });
        const data = await res.json();

        const msg = `
            <b>KẾT NỐI POWER BI THÀNH CÔNG!</b><br><br>
            Sử dụng URL sau trong Power BI Desktop (Get Data from Web):<br>
            <div class="bg-light p-2 my-2 border rounded text-break small" id="pbiUrl">${data.url}</div>
            <button class="btn btn-sm btn-outline-primary mb-3" onclick="copyPbiUrl()">Copy URL</button><br>
            <b>Hướng dẫn:</b><br>
            ${data.instructions.map(i => `<div class="small">${i}</div>`).join('')}
        `;

        const plotArea = document.getElementById('plotArea');
        plotArea.innerHTML = `<div class="p-4">${msg}</div>`;
    } catch (e) { alert(e.message); }
}

function copyPbiUrl() {
    const url = document.getElementById('pbiUrl').innerText;
    navigator.clipboard.writeText(url).then(() => alert("Đã copy URL!"));
}