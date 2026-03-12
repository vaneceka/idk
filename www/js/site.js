function initCheckboxToggling(name, allCheckbox) {
    const element = document.getElementById(allCheckbox)
    if (!element) {
        return;
    }

    const checkboxes = document.querySelectorAll('input[type="checkbox"][name="' + name + '"]');

    let allChecked = true;
    for (const checkbox of checkboxes) {
        if (!checkbox.checked) {
            allChecked = false;
            break;
        }
    }

    element.checked = allChecked;

    element.addEventListener('click', (e) => {
        const checked = e.target.checked;
        checkboxes.forEach(checkbox => checkbox.checked = checked);
    });

    for (const checkbox of checkboxes) {
        checkbox.addEventListener('click', (e) => {
            let allChecked = true;
            for (const checkbox of checkboxes) {
                if (!checkbox.checked) {
                    allChecked = false;
                    break;
                }
            }
            element.checked = allChecked;
        })
    }
}

function initToggleSwitching(select, doc, table, firstKey = 'document', required = false) {
    const docEl = document.getElementById(doc);
    const tableEl = document.getElementById(table);

    document.getElementById(select).addEventListener('change', (e) => {
        if (e.target.value === firstKey) {
            docEl.style.display = 'block';
            tableEl.style.display = 'none';
            if (required) {
                docEl.querySelectorAll('input').forEach(e => e.required = true);
                tableEl.querySelectorAll('input').forEach(e => e.required = false);
            }
        } else {
            docEl.style.display = 'none';
            tableEl.style.display = 'block';
            if (required) {
                docEl.querySelectorAll('input').forEach(e => e.required = false);
                tableEl.querySelectorAll('input').forEach(e => e.required = true);
            }
        }
    });
}