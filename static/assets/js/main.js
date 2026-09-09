
document.addEventListener('DOMContentLoaded', function () {
    initUploadForm();
    initProgressForm();
    loadTopicProgress(1); 
    renderProgressChart();
});

function initUploadForm() {
    const uploadForm = document.getElementById('uploadForm');
    const uploadStatus = document.getElementById('uploadStatus');

    if (!uploadForm) return;

    uploadForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const fileInput = document.getElementById('fileInput');
        if (!fileInput.files || fileInput.files.length === 0) {
            alert('Vui lòng chọn file trước khi gửi!');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        uploadStatus.innerText = 'Đang tải file lên...';

        try {
            const res = await fetch('/api/submissions/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.success) {
                uploadStatus.innerHTML = `<span style="color: green;"> Upload thành công: ${data.data.filename}</span>`;
                fileInput.value = '';
            } else {
                uploadStatus.innerHTML = `<span style="color: red;"> Lỗi: ${data.message}</span>`;
            }
        } catch (err) {
            console.error(err);
            uploadStatus.innerHTML = `<span style="color: red;"> Lỗi kết nối máy chủ!</span>`;
        }
    });
}

async function loadTopicProgress(topicId) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const milestoneList = document.getElementById('milestoneList');

    try {
        const res = await fetch(`/api/topics/${topicId}/progress`);
        const result = await res.json();

        if (result.success) {
            const milestones = result.milestones || [];
            
            let latestPercentage = 0;
            if (milestones.length > 0) {
                latestPercentage = milestones[milestones.length - 1].percentage;
            }
            if (progressBar) {
                progressBar.style.width = `${latestPercentage}%`;
            }
            if (progressText) {
                progressText.innerText = `${latestPercentage}%`;
            }
            if (milestoneList) {
                milestoneList.innerHTML = milestones.map(m => `
                    <li>
                        <strong>[${m.percentage}%] ${m.title}</strong> - <em>${m.note}</em> 
                        <small>(${m.created_at})</small>
                    </li>
                `).join('');
            }
        }
    } catch (err) {
        console.error("Lỗi tải tiến độ:", err);
    }
}

function initProgressForm() {
    const progressForm = document.getElementById('progressForm');
    if (!progressForm) return;

    progressForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const topicId = document.getElementById('topicIdInput').value || 1;
        const title = document.getElementById('milestoneTitle').value;
        const percentage = document.getElementById('milestonePct').value;
        const note = document.getElementById('milestoneNote').value;

        try {
            const res = await fetch(`/api/topics/${topicId}/progress`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: title,
                    percentage: parseInt(percentage),
                    note: note
                })
            });
            const data = await res.json();

            if (data.success) {
                alert('Cập nhật tiến độ thành công!');
                loadTopicProgress(topicId);
                renderProgressChart();
            }
        } catch (err) {
            console.error("Lỗi lưu tiến độ:", err);
        }
    });
}

let chartInstance = null; 

async function renderProgressChart() {
    const chartCanvas = document.getElementById('progressChart');
    if (!chartCanvas) return;

    try {
        const res = await fetch('/api/dashboard/progress');
        const result = await res.json();

        if (result.success) {
            const data = result.data;
            const labels = data.map(item => `Đề tài ${item.topic_id}`);
            const percentages = data.map(item => item.average_percentage);

            if (chartInstance) {
                chartInstance.destroy();
            }

            const ctx = chartCanvas.getContext('2d');
            chartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '% Hoàn thành trung bình',
                        data: percentages,
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }
    } catch (err) {
        console.error("Lỗi vẽ biểu đồ:", err);
    }
}