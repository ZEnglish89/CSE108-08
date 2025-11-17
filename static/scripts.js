// static/scripts.js
function openEditModal(id, title, teacher, time, capacity) {
    document.getElementById('editCourseForm').action = `/admin/edit_course/${id}`;
    document.getElementById('editTitle').value = title;
    document.getElementById('editTime').value = time;
    document.getElementById('editCapacity').value = capacity;

    // Populate teacher dropdown
    fetch('/api/instructors')
      .then(response => response.json())
      .then(data => {
        const select = document.getElementById('editTeacher');
        select.innerHTML = '';
        data.forEach(instr => {
          const option = document.createElement('option');
          option.value = instr.username;
          option.text = instr.username;
          if (instr.username === teacher) option.selected = true;
          select.appendChild(option);
        });
      });

    // Show modal (not Bootstrap — just change display style)
    document.getElementById('editModal').style.display = 'flex';
  }

  function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
  }

function openUserModal(id = null, username = '', email = '', role = '') {
  const form = document.getElementById('userForm');

  if (id) {
    form.action = `/admin/users/edit/${id}`;
    document.getElementById('userModalTitle').innerText = 'Edit User';
    document.getElementById('password').required = false;
  } else {
    form.action = '/admin/users';
    document.getElementById('userModalTitle').innerText = 'Create New User';
    document.getElementById('password').required = true;
  }

  document.getElementById('username').value = username;
  document.getElementById('email').value = email;
  document.getElementById('password').value = '';
  document.getElementById('role').value = role || 'student';

  document.getElementById('userModal').style.display = 'flex';
}

function closeUserModal() {
  document.getElementById('userModal').style.display = 'none';
}