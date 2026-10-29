# scratch/update_notif_ui.py
import os
import re

print("--- 1. Updating templates/student.html ---")
with open('templates/student.html', 'r', encoding='utf-8') as f:
    student_html = f.read()

target_student = """                    {% if notifications %}
                        {% for notif in notifications %}
                        <li>
                            <a class="dropdown-item p-3 border-bottom d-flex gap-3 align-items-start notif-dropdown-item {% if not notif.is_read %}bg-light{% endif %}" 
                               href="javascript:void(0)" 
                               data-notif-id="{{ notif.id }}" 
                               data-notif-content="{{ notif.content | e }}" 
                               onclick="event.preventDefault(); window.handleNotifItemClick(this, event)">
                                <div class="bg-primary-subtle text-primary rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width: 32px; height: 32px;"><i class="fa-regular fa-bell"></i></div>
                                <div>
                                    <div class="fw-bold small text-dark mb-1 d-flex align-items-center justify-content-between">
                                        <span>Thông báo hệ thống</span>
                                        {% if not notif.is_read %}
                                            <span class="badge bg-danger rounded-circle p-1" style="width:8px; height:8px;"></span>
                                        {% endif %}
                                    </div>
                                    <div class="small text-muted mb-1" style="line-height: 1.4; white-space: normal;">{{ notif.content.split('|||')[0] | striptags | truncate(80) }}</div>
                                    <div class="text-muted" style="font-size: 10px;">{{ notif.created_at.strftime('%d/%m/%Y %H:%M') if notif.created_at else '' }}</div>
                                </div>
                            </a>
                        </li>
                        {% endfor %}
                    {% endif %}"""

replacement_student = """                    {% if notifications %}
                        {% for notif in notifications %}
                        {% set is_faculty_approved = 'Khoa' in notif.content and ('phê duyệt' in notif.content or 'ĐÃ PHÊ DUYỆT' in notif.content) %}
                        {% set is_faculty_revision = 'Khoa' in notif.content and ('chỉnh sửa' in notif.content or 'YÊU CẦU' in notif.content) %}
                        {% set is_lecturer_review = 'Giảng viên' in notif.content or 'GV' in notif.content or 'đánh giá' in notif.content or 'hướng dẫn' in notif.content %}
                        <li>
                            <a class="dropdown-item p-3 border-bottom d-flex gap-3 align-items-start notif-dropdown-item {% if not notif.is_read %}bg-light{% endif %}" 
                               href="javascript:void(0)" 
                               data-notif-id="{{ notif.id }}" 
                               data-notif-content="{{ notif.content | e }}" 
                               onclick="event.preventDefault(); window.handleNotifItemClick(this, event)">
                                <div class="{% if is_faculty_approved %}bg-success-subtle text-success{% elif is_faculty_revision %}bg-danger-subtle text-danger{% elif is_lecturer_review %}bg-primary-subtle text-primary{% else %}bg-secondary-subtle text-secondary{% endif %} rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width: 32px; height: 32px;">
                                    <i class="{% if is_faculty_approved %}fa-solid fa-stamp{% elif is_faculty_revision %}fa-solid fa-triangle-exclamation{% elif is_lecturer_review %}fa-solid fa-chalkboard-user{% else %}fa-regular fa-bell{% endif %}"></i>
                                </div>
                                <div class="flex-grow-1" style="min-width: 0;">
                                    <div class="fw-bold small mb-1 d-flex align-items-center justify-content-between">
                                        <span class="{% if is_faculty_approved %}text-success{% elif is_faculty_revision %}text-danger{% elif is_lecturer_review %}text-primary{% else %}text-dark{% endif %}">
                                            {% if is_faculty_approved %}
                                                <i class="fa-solid fa-circle-check me-1"></i>Khoa đã phê duyệt
                                            {% elif is_faculty_revision %}
                                                <i class="fa-solid fa-triangle-exclamation me-1"></i>Khoa yêu cầu sửa
                                            {% elif is_lecturer_review %}
                                                <i class="fa-solid fa-user-tie me-1"></i>Đánh giá từ GVHD
                                            {% else %}
                                                Thông báo hệ thống
                                            {% endif %}
                                        </span>
                                        {% if not notif.is_read %}
                                            <span class="badge bg-danger rounded-circle p-1" style="width:8px; height:8px;"></span>
                                        {% endif %}
                                    </div>
                                    <div class="small text-muted mb-1" style="line-height: 1.4; white-space: normal;">{{ notif.content.split('|||')[0] | striptags | replace('\n', ' ') | truncate(95) }}</div>
                                    <div class="text-muted" style="font-size: 10px;">{{ notif.created_at.strftime('%d/%m/%Y %H:%M') if notif.created_at else '' }}</div>
                                </div>
                            </a>
                        </li>
                        {% endfor %}
                    {% endif %}"""

# Normalize \r\n for matching
student_html_norm = student_html.replace('\r\n', '\n')
target_student_norm = target_student.replace('\r\n', '\n')
replacement_student_norm = replacement_student.replace('\r\n', '\n')

if target_student_norm in student_html_norm:
    student_html_norm = student_html_norm.replace(target_student_norm, replacement_student_norm, 1)
    with open('templates/student.html', 'w', encoding='utf-8') as f:
        f.write(student_html_norm)
    print("Updated templates/student.html successfully!")
else:
    print("Target not found in templates/student.html!")


print("\n--- 2. Updating templates/layouts/student_layout.html ---")
if os.path.exists('templates/layouts/student_layout.html'):
    with open('templates/layouts/student_layout.html', 'r', encoding='utf-8') as f:
        layout_html = f.read()
    
    target_layout = """                            {% if notifications %}
                                {% for notif in notifications %}
                                <li>
                                    <a class="dropdown-item p-3 border-bottom d-flex gap-3 align-items-start notif-dropdown-item {% if not notif.is_read %}bg-light{% endif %}" 
                                       href="javascript:void(0)" 
                                       data-notif-id="{{ notif.id }}" 
                                       data-notif-content="{{ notif.content | e }}" 
                                       onclick="event.preventDefault(); window.handleNotifItemClick(this, event)">
                                        <div class="bg-primary-subtle text-primary rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width: 32px; height: 32px;"><i class="fa-regular fa-bell"></i></div>
                                        <div>
                                            <div class="fw-bold small text-dark mb-1 d-flex align-items-center justify-content-between">
                                                <span>Thông báo hệ thống</span>
                                                {% if not notif.is_read %}
                                                    <span class="badge bg-danger rounded-circle p-1" style="width:8px; height:8px;"></span>
                                                {% endif %}
                                            </div>
                                            <div class="small text-muted mb-1" style="line-height: 1.4; white-space: normal;">{{ notif.content.split('|||')[0] | striptags | truncate(80) }}</div>
                                            <div class="text-muted" style="font-size: 10px;">{{ notif.created_at.strftime('%d/%m/%Y %H:%M') if notif.created_at else '' }}</div>
                                        </div>
                                    </a>
                                </li>
                                {% endfor %}
                            {% endif %}"""

    replacement_layout = """                            {% if notifications %}
                                {% for notif in notifications %}
                                {% set is_faculty_approved = 'Khoa' in notif.content and ('phê duyệt' in notif.content or 'ĐÃ PHÊ DUYỆT' in notif.content) %}
                                {% set is_faculty_revision = 'Khoa' in notif.content and ('chỉnh sửa' in notif.content or 'YÊU CẦU' in notif.content) %}
                                {% set is_lecturer_review = 'Giảng viên' in notif.content or 'GV' in notif.content or 'đánh giá' in notif.content or 'hướng dẫn' in notif.content %}
                                <li>
                                    <a class="dropdown-item p-3 border-bottom d-flex gap-3 align-items-start notif-dropdown-item {% if not notif.is_read %}bg-light{% endif %}" 
                                       href="javascript:void(0)" 
                                       data-notif-id="{{ notif.id }}" 
                                       data-notif-content="{{ notif.content | e }}" 
                                       onclick="event.preventDefault(); window.handleNotifItemClick(this, event)">
                                        <div class="{% if is_faculty_approved %}bg-success-subtle text-success{% elif is_faculty_revision %}bg-danger-subtle text-danger{% elif is_lecturer_review %}bg-primary-subtle text-primary{% else %}bg-secondary-subtle text-secondary{% endif %} rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width: 32px; height: 32px;">
                                            <i class="{% if is_faculty_approved %}fa-solid fa-stamp{% elif is_faculty_revision %}fa-solid fa-triangle-exclamation{% elif is_lecturer_review %}fa-solid fa-chalkboard-user{% else %}fa-regular fa-bell{% endif %}"></i>
                                        </div>
                                        <div class="flex-grow-1" style="min-width: 0;">
                                            <div class="fw-bold small mb-1 d-flex align-items-center justify-content-between">
                                                <span class="{% if is_faculty_approved %}text-success{% elif is_faculty_revision %}text-danger{% elif is_lecturer_review %}text-primary{% else %}text-dark{% endif %}">
                                                    {% if is_faculty_approved %}
                                                        <i class="fa-solid fa-circle-check me-1"></i>Khoa đã phê duyệt
                                                    {% elif is_faculty_revision %}
                                                        <i class="fa-solid fa-triangle-exclamation me-1"></i>Khoa yêu cầu sửa
                                                    {% elif is_lecturer_review %}
                                                        <i class="fa-solid fa-user-tie me-1"></i>Đánh giá từ GVHD
                                                    {% else %}
                                                        Thông báo hệ thống
                                                    {% endif %}
                                                </span>
                                                {% if not notif.is_read %}
                                                    <span class="badge bg-danger rounded-circle p-1" style="width:8px; height:8px;"></span>
                                                {% endif %}
                                            </div>
                                            <div class="small text-muted mb-1" style="line-height: 1.4; white-space: normal;">{{ notif.content.split('|||')[0] | striptags | replace('\n', ' ') | truncate(95) }}</div>
                                            <div class="text-muted" style="font-size: 10px;">{{ notif.created_at.strftime('%d/%m/%Y %H:%M') if notif.created_at else '' }}</div>
                                        </div>
                                    </a>
                                </li>
                                {% endfor %}
                            {% endif %}"""

    layout_html_norm = layout_html.replace('\r\n', '\n')
    target_layout_norm = target_layout.replace('\r\n', '\n')
    replacement_layout_norm = replacement_layout.replace('\r\n', '\n')

    if target_layout_norm in layout_html_norm:
        layout_html_norm = layout_html_norm.replace(target_layout_norm, replacement_layout_norm, 1)
        with open('templates/layouts/student_layout.html', 'w', encoding='utf-8') as f:
            f.write(layout_html_norm)
        print("Updated templates/layouts/student_layout.html successfully!")
    else:
        print("Target not found in templates/layouts/student_layout.html!")

