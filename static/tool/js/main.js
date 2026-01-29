/**
 * tool/assets/js/main.js - Phiên bản Fix lỗi AI & Giao diện
 */

let datasetId = null;
let currentCols = [];
let selectedMultiCols = new Set();
let lastUsedCols = [];
let tempChartType = null;

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

function sendPrompt(txt) { 
    if(els.chatInput) { els.chatInput.value = txt; sendChat(); }
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
    if(!datasetId) return alert("Vui lòng tải file trước!");
    tempChartType = type;
    
    const config = {
        'selection': { title: 'Chọn dữ liệu', btn: 'Lưu lựa chọn' },
        'grouped':   { title: 'Vẽ Ghép nhóm (Grouped)', btn: 'Vẽ ngay' },
        'stacked':   { title: 'Vẽ Cột chồng (Stacked)', btn: 'Vẽ ngay' }
    };
    const cfg = config[type] || config['selection'];
    if(getEl('multiTitle')) getEl('multiTitle').innerText = cfg.title;
    if(els.btnConfirmText) els.btnConfirmText.innerText = cfg.btn;
    
    if(els.colSearchInput) els.colSearchInput.value = "";
    renderDualList();
    if(els.multiModal) els.multiModal.style.display = 'flex';
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
    if(arr.length < 1) return alert("Chọn ít nhất 1 cột!");
    lastUsedCols = arr;
    
    if(els.colDisplay) {
        els.colDisplay.style.color = "#fff";
        els.colDisplay.innerText = arr.length === 1 ? arr[0] : `${arr[0]} (+${arr.length-1} cột)`;
    }
    if(els.multiModal) els.multiModal.style.display = 'none';
    if(tempChartType && tempChartType !== 'selection') drawPlot(tempChartType, arr);
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
    if(els.plotArea) els.plotArea.innerHTML = '<div class="loader" style="margin:auto"></div>';
    try {
        const res = await fetch('/api/plot', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({ dataset_id: datasetId, plots: [{type, col: cols[0], cols: cols}] })
        });
        const d = await res.json();
        
        if(d.images && d.images.length && els.plotArea) {
            els.plotArea.innerHTML = `<img src="${d.images[0]}" class="fade-in">`;
            if(getEl('autoAnalyze') && getEl('autoAnalyze').checked) {
                if(els.chatBox && !els.chatBox.classList.contains('open')) toggleChat();
                sendPrompt(`Phân tích biểu đồ ${type}: ${cols.join(', ')}`);
            }
        } else if(els.plotArea) {
            els.plotArea.innerHTML = "<div class='empty-state'>Lỗi dữ liệu.</div>";
        }
    } catch(e) { 
        if(els.plotArea) els.plotArea.innerHTML = "Lỗi Vẽ: " + e.message; 
    }
}

// --- CHAT & UTILS ---
async function sendChat() {
    if(!els.chatInput) return;
    const txt = els.chatInput.value.trim();
    if (!txt) return;
    addMsg(txt, 'user'); els.chatInput.value = '';
    
    // [FIX LỖI NULL] Lấy model an toàn
    const modelEl = getEl('aiModel');
    const modelVal = modelEl ? modelEl.value : "llama-3.3-70b-versatile";
    
    const botId = addMsg('<div class="loader" style="width:15px;height:15px;border-width:2px"></div>', 'bot');
    
    try {
        const res = await fetch('/api/chat', {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ 
                prompt: txt, dataset_id: datasetId, cols: lastUsedCols, 
                selected_col: lastUsedCols[0], model: modelVal 
            })
        });
        const data = await res.json();
        const b = getEl(botId);
        if(b) { 
            b.innerHTML = data.reply.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br>');
            if(data.suggestions) {
                const con = document.querySelector('.suggestion-chips');
                if(con) {
                    con.innerHTML = '';
                    data.suggestions.forEach(s => {
                        const sp = document.createElement('span'); sp.innerText = s; 
                        sp.onclick = () => sendPrompt(s); con.appendChild(sp);
                    });
                }
            }
        }
    } catch(e) { 
        const b = getEl(botId); 
        if(b) b.innerHTML = `<span style='color:red'>Lỗi AI: ${e.message}</span>`; 
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

function openCleanModal() { if(datasetId && els.cleanModal) els.cleanModal.style.display='flex'; }
function closeModal(id) { const el = getEl(id); if(el) el.style.display='none'; }

async function runClean() {
    try {
        const btn = document.querySelector('#cleanModal .btn-primary');
        if(btn) { btn.innerText = "Đang xử lý..."; btn.disabled = true; }
        
        const res = await fetch('/api/clean', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({ 
                dataset_id: datasetId, 
                drop_na: getEl('chkNa')?.checked, 
                drop_duplicates: getEl('chkDup')?.checked 
            })
        });
        const d = await res.json();
        if(d.error) throw new Error(d.error);
        alert(`Đã làm sạch!\nTrước: ${d.old_shape[0]}\nSau: ${d.new_shape[0]}`);
        if(els.cleanModal) els.cleanModal.style.display='none';
    } catch(e) { alert("Lỗi: " + e.message); } 
    finally { 
        const btn = document.querySelector('#cleanModal .btn-primary'); 
        if(btn){ btn.innerText="Thực hiện"; btn.disabled=false; }
    }
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