(function () {
    function initContainer(container) {
        if (container.dataset.multiTextInit === '1')
            return;

        container.dataset.multiTextInit = '1';

        const fieldName = container.querySelector('input[name]')?.name || 'sources';
        const addBtn = container.querySelector('button:not(.remove-source)');

        const getRows = () =>
            Array.from(container.querySelectorAll('.source-row'));

        function cloneRow() {
            const rows = getRows();
            if (!rows.length)
                return;

            const last = rows[rows.length - 1];
            const clone = last.cloneNode(true);

            const input = clone.querySelector(`input[name="${fieldName}"]`);

            if (input)
                input.value = '';

            const prefix = container.dataset.rowIdPrefix;

            if (prefix)
                clone.id = `${prefix}-${Date.now()}`;

            container.insertBefore(clone, addBtn);
        }

        addBtn?.addEventListener('click', e => {
            e.preventDefault();
            cloneRow();
        });

        container.addEventListener('click', e => {
            const btn = e.target.closest('button.remove-source');

            if (!btn)
                return;

            const row = btn.closest('.source-row');

            if (!row)
                return;

            const rows = getRows();

            if (rows.length > 1) {
                row.remove();
            } else {
                const input = row.querySelector(`input[name="${fieldName}"]`);

                if (input)
                    input.value = '';
            }
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-row-id-prefix]').forEach(initContainer);
    });
})();