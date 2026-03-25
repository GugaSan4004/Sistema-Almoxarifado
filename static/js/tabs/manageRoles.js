{
    const rolesDataElement = document.getElementById('roles-data-json');
    const allTabsElement = document.getElementById('all-tabs-json');

    if (rolesDataElement && allTabsElement) {
        const allTabs = JSON.parse(allTabsElement.textContent);
        const rolesData = JSON.parse(rolesDataElement.textContent);

        const modeToggle = document.getElementById('mode_toggle');
        const roleInputContainer = document.getElementById('role_input_container');
        const tabCheckboxes = document.querySelectorAll('.tab-checkbox');
        const formAction = document.getElementById('form_action');
        const deleteBtn = document.getElementById('delete_btn');

        function updatePermissions() {
            const roleSelect = document.getElementById('role_select');
            if (!roleSelect) return;

            const selectedRoleId = parseInt(roleSelect.value);
            const selectedRole = rolesData.find(r => r.id === selectedRoleId);

            tabCheckboxes.forEach(cb => {
                if (selectedRole && selectedRole.tabs.includes(cb.value)) {
                    cb.checked = true;
                } else {
                    cb.checked = false;
                }
            });

            if (selectedRoleId === 0 || selectedRoleId === 1) {
                deleteBtn.classList.add('hidden');
            } else {
                deleteBtn.classList.remove('hidden');
            }
        }

        function renderUI() {
            if (modeToggle.checked) {
                let options = rolesData.map(r => `<option value="${r.id}">${escapeHtml(r.name)}</option>`).join('');
                roleInputContainer.innerHTML = `
                    <label for="role_select" class="font-semibold text-gray-700">Selecione o Cargo</label>
                    <select name="role_id" id="role_select" class="border border-gray-300 rounded-md p-2 bg-white" onchange="updatePermissions()">
                        ${options}
                    </select>
                `;
                updatePermissions();
            } else {
                roleInputContainer.innerHTML = `
                <label for="role_name" class="font-semibold text-gray-700">Nome do Cargo</label>
                <input type="text" name="role_name" id="role_name" class="border border-gray-300 rounded-md p-2" required>
                `;
                tabCheckboxes.forEach(cb => {
                    cb.checked = false;
                    cb.disabled = false;
                });
                deleteBtn.classList.add('hidden');
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        window.submitDelete = function () {
            if (confirm("Tem certeza que deseja excluir este cargo?")) {
                formAction.value = "delete";
                document.getElementById('manage_roles_form').requestSubmit();
                setTimeout(() => formAction.value = "save", 100);
            }
        }

        modeToggle.addEventListener('change', renderUI);
        renderUI();
    }
}
