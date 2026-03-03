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
    aiFab: getEl('aiFab'),
    multiModal: getEl('multiModal'),
    cleanModal: getEl('cleanModal'),
    colSearchInput: getEl('colSearchInput'),
    btnConfirmText: getEl('btnConfirmText'),
    availableList: getEl('availableList'),
    selectedList: getEl('selectedList'),
    selectedCountDisplay: getEl('selectedCountDisplay')
};

// --- EVENTS ---
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll(".accordion-header").forEach(header => {
        header.onclick = (e) => {
            e.preventDefault();
            header.parentElement.classList.toggle("active");
        };
    });
});

window.onclick = function(event) {
    if (event.target == els.multiModal) els.multiModal.style.display = "none";
    if (event.target == els.cleanModal) els.cleanModal.style.display = "none";
};

if(els.chatInput) {
    els.chatInput.addEventListener("keypress", (e) => { if(e.key==="Enter"){ e.preventDefault(); sendChat(); }});
}

function toggleChat() { 
    if(els.chatBox) {
        els.chatBox.classList.toggle('open'); 
        if(els.aiFab) els.aiFab.style.display = els.chatBox.classList.contains('open') ? 'none' : 'flex';
    }
}

function sendPrompt(text) {
  const input = document.getElementById('chatInput');
  input.value = text;
  sendChat();
}

// --- UPLOAD ---
if(els.fileInput) {
    els.fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const fd = new FormData(); fd.append('file', file);
        try {
            els.uploadText.innerText = "Đang tải lên...";
            els.fileStatus.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang xử lý...`;
            const res = await fetch('/api/upload', {method:'POST', body:fd});
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            
            datasetId = data.dataset_id;
            currentCols = data.columns || [];
            selectedMultiCols.clear(); lastUsedCols = [];
            
            if(els.colDisplay) {
                els.colDisplay.innerText = "Chưa chọn cột nào";
                els.colDisplay.style.color = "#9ca3af";
            }
            
            els.fileStatus.innerHTML = `<i class="fa-solid fa-file-excel"></i> <strong>${data.original_filename}</strong>`;
            els.uploadText.innerText = "Đổi file khác";
            
            if(confirm("Tải thành công! Có muốn làm sạch dữ liệu không?")) openCleanModal();
        } catch(err) { 
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
        'grouped':   { title: 'Cột Ghép nhóm – chọn nhiều cột', btn: 'Vẽ ngay' },
        'stacked':   { title: 'Cột Chồng Dọc – chọn nhiều cột', btn: 'Vẽ ngay' },
        'stacked_h': { title: 'Cột Chồng Ngang – chọn nhiều cột', btn: 'Vẽ ngay' },
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
    if(els.availableList) els.availableList.innerHTML = '';
    if(els.selectedList) els.selectedList.innerHTML = '';
    
    selectedMultiCols.forEach(col => {
        const div = document.createElement('div');
        div.className = 'dual-item target';
        div.innerHTML = `<span>${col}</span><i class="fa-solid fa-xmark remove-icon"></i>`;
        div.onclick = () => { selectedMultiCols.delete(col); renderDualList(); };
        if(els.selectedList) els.selectedList.appendChild(div);
    });
    
    currentCols.forEach(col => {
        if(selectedMultiCols.has(col)) return;
        if(searchVal && !col.toLowerCase().includes(searchVal)) return;
        const div = document.createElement('div');
        div.className = 'dual-item source';
        div.innerHTML = `<span>${col}</span>`;
        div.onclick = () => { selectedMultiCols.add(col); renderDualList(); };
        if(els.availableList) els.availableList.appendChild(div);
    });
    if(els.selectedCountDisplay) els.selectedCountDisplay.innerText = selectedMultiCols.size;
}

if(els.colSearchInput) els.colSearchInput.oninput = () => renderDualList();
function clearAllSelection() { selectedMultiCols.clear(); renderDualList(); }

function applyMulti() {
    const arr = Array.from(selectedMultiCols);
    // Đọc từ cả window.tempChartType (set bởi override trong HTML) lẫn biến let
    const chartType = window.tempChartType || tempChartType;
    const multiColTypes = ['grouped', 'stacked', 'stacked_h'];
    if (arr.length < 1) return alert("Chọn ít nhất 1 cột!");
    if (multiColTypes.includes(chartType) && arr.length < 2)
        return alert("Biểu đồ so sánh cần chọn ít nhất 2 cột!");
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
        drawPlot(chartType, arr);
    }
}

// --- VẼ BIỂU ĐỒ ---
async function setType(type) { 
    if(!datasetId) return alert("Chưa có file!");
    if(!lastUsedCols || lastUsedCols.length === 0) {
        if(confirm("Chưa chọn dữ liệu. Mở danh sách chọn?")) openMultiModal('selection');
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
      body: JSON.stringify({ dataset_id: datasetId, plots })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    if (data.images && data.images.length) {
      document.getElementById('plotArea').innerHTML =
        `<img src="${data.images[0]}" class="fade-in" style="max-width:100%;height:auto;">`;
      if (document.getElementById('autoAnalyze')?.checked) {
        if (document.getElementById('chatBox')?.classList.contains('d-none')) toggleChat();
        sendPrompt(`Phân tích biểu đồ ${type} cho dữ liệu: ${cols.slice(0,3).join(', ')}${cols.length > 3 ? '...' : ''}`);
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

  const modelEl = document.getElementById('aiModel');
  const modelVal = modelEl ? modelEl.value : "llama-3.3-70b-versatile";

  const botId = addMsg('<div class="loader" style="width:15px;height:15px;border-width:2px"></div>', 'bot');

  try {
    const res = await fetch('/api/chat', {
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
    if (botMsg) botMsg.innerHTML = `<span style='color:red'>Lỗi AI: ${e.message}</span>`;
  }
}

function addMsg(txt, role) {
    const id = 'msg-' + Date.now();
    if(els.messages) {
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
    if(img) { const a = document.createElement('a'); a.href = img.src; a.download = 'chart.png'; a.click(); } 
    else alert("Chưa có biểu đồ!"); 
}

async function exportReport() {
    const img = els.plotArea ? els.plotArea.querySelector('img') : null;
    if(!img) return alert("Vui lòng vẽ biểu đồ trước!");
    const btn = document.querySelector('.top-actions .btn-primary');
    if(btn) { var old = btn.innerHTML; btn.innerHTML = "Đang tạo..."; }
    
    try {
        await fetch('/api/generate_doc', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({ 
                image: img.src, col_name: lastUsedCols.join(', '), 
                user_question: "Phân tích", dataset_id: datasetId 
            })
        }).then(r=>r.blob()).then(b=>{
            const a=document.createElement('a'); a.href=window.URL.createObjectURL(b); a.download=`Report_${Date.now()}.docx`; a.click();
        });
    } catch(e) { alert("Lỗi: " + e.message); } 
    finally { if(btn) btn.innerHTML = old; }
}