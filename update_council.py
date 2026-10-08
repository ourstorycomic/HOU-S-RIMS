import os

path = r'd:\HOU-S-RIMS\templates\faculty\council.html'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if i == 22: # 0-indexed, so line 23
        new_lines.append('''                                    <div class="collapse" id="councilCollapse{{ c.id }}">
                                        <div class="card-body bg-light border-top p-3">
                                            <div class="row g-3">
                                                <div class="col-md-6">
                                                    <div class="small fw-bold text-muted mb-2">THÔNG TIN HỌP:</div>
                                                    <div class="small mb-1"><i class="fa-regular fa-clock me-2"></i>{{ c.meeting_time.strftime('%H:%M') if c.meeting_time else '--:--' }} | {{ c.meeting_date.strftime('%d/%m/%Y') if c.meeting_date else '--/--/----' }}</div>
                                                    <div class="small mb-1"><i class="fa-solid fa-location-dot me-2"></i>{{ c.location or 'Chưa xác định' }}</div>
                                                    <div class="small mb-2"><i class="fa-solid fa-hashtag me-2"></i>QĐ: {{ c.decision_number or 'Chưa có' }}</div>
                                                    
                                                    <div class="small fw-bold text-muted mt-3 mb-2">DANH SÁCH THÀNH VIÊN:</div>
                                                    <ul class="list-group small">
                                                        {% if c.members %}
                                                            {% for m in c.members %}
                                                            <li class="list-group-item bg-transparent border-0 py-1 ps-0 text-dark">
                                                                <span class="badge bg-secondary me-2">{% if m.role == 'president' %}Chủ tịch{% elif m.role == 'secretary' %}Thư ký{% else %}Ủy viên{% endif %}</span> 
                                                                {{ m.mentor.full_name if m.mentor else 'N/A' }}
                                                            </li>
                                                            {% endfor %}
                                                        {% else %}
                                                            <li class="list-group-item bg-transparent border-0 py-1 ps-0 text-muted">Chưa cập nhật thành viên</li>
                                                        {% endif %}
                                                    </ul>
                                                </div>
                                                <div class="col-md-6 border-start">
                                                    <div class="small fw-bold text-muted mb-2">ĐỀ TÀI / NHÓM BÁO CÁO:</div>
                                                    <ul class="list-group small">
                                                        {% if c.topics %}
                                                            {% for t in c.topics %}
                                                            <li class="list-group-item bg-transparent border-0 py-1 ps-0 text-dark">
                                                                <i class="fa-solid fa-caret-right me-1 text-primary"></i> <strong>{{ t.title }}</strong><br>
                                                                <span class="text-muted ms-3">Nhóm: {{ t.group.name if t.group else 'N/A' }}</span>
                                                            </li>
                                                            {% endfor %}
                                                        {% else %}
                                                            <li class="list-group-item bg-transparent border-0 py-1 ps-0 text-muted">Chưa phân công đề tài.</li>
                                                        {% endif %}
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                    </div>\n''')
        skip = True
    elif i == 30:
        skip = False
    elif not skip:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
