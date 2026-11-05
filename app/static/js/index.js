window.addEventListener('DOMContentLoaded', () => {
    const sonoffTable = document.querySelector(".sonoff-table");
    const schemeTable = document.querySelector(".scheme-table");
    if (sonoffTable) new SonoffTable(sonoffTable, tableRows);
    if (schemeTable) new SchemeTable(schemeTable, tableRows);

    const logPanel = document.querySelector("#log-panel");
    if (logPanel) {
        const menu = document.querySelector("#log-date-menu");
        const button = document.querySelector("#log-date-button");
        button.addEventListener("click", () => {
            menu.style.removeProperty("inset");
            menu.style.removeProperty("margin");
        });
        logPanel.addEventListener("contextmenu", event => {
            if (!menu.contains(event.target)) openContextMenu(menu, event);
        });
    }
});


function openContextMenu(menu, event) {
    event.preventDefault();
    if (!menu.matches(":popover-open")) menu.showPopover();
    const x = Math.max(0, Math.min(event.clientX, window.innerWidth - menu.offsetWidth));
    const y = Math.max(0, Math.min(event.clientY, window.innerHeight - menu.offsetHeight));
    menu.style.margin = "0";
    menu.style.inset = `${y}px auto auto ${x}px`;
}


class TableBase {
    constructor(table_data) {
        const table = table_data.html_table;
        if (table_data.header) table.innerHTML = table_data.header;
        for (const [index, property] of table_data.properties.entries()) {
            const row = table.insertRow();
            row.insertCell().textContent = table_data.labels[index];
            for (const item of table_data.data) {
                const cell = row.insertCell();
                cell.className = table_data.types[index];
                cell.dataset[table_data.data_label] = `${property}-${item.id}`;
                this.set_cell_content_bg(cell, item[property]);
            }
        }

        this.table_data = table_data;
        this.socket = io("/" + table_data.sio_namespace);
        this.misc_cell_updates = {}

        // Receive table update events from server
        this.socket.on("json", (data) => {
            const td = document.querySelector(`[data-${this.table_data.data_label}="${data.id}"]`);
            if (td)
                // data.id maps 101 with cell-id (e.g. id = active)
                this.set_cell_content_bg(td, data.value);
            else if (this.misc_cell_updates) {
                // a miscellaneous event is connected with a cell (e.g. sonoffactive)
                const [event, id] = data.id.split("-");
                if (this.misc_cell_updates[event]) {
                    this.misc_cell_update(this.misc_cell_updates[event].row, id, this.misc_cell_updates[event].type, data.value);
                }
            }
        });
        // Send table update events to server
        table_data.html_table.addEventListener("click", e => {
            const td = e.target;
            if (td.classList.contains("green-white") || td.classList.contains("green-red-aan-uit")) {
                this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: td.textContent === "AAN"})
            } else if (td.classList.contains("input-locatie")) {
                let text = prompt("Geef een locatie");
                if (text) this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: text})
            } else if (td.classList.contains("input-sonoff-id")) {
                let text = prompt("Geef een sonoff id (e.g. sonoff21)");
                if (text) this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: text})
            } else if (td.classList.contains("input-schema")) {
                let text = prompt("Geef één of meerdere schemas, gescheiden door een komma.  \n0 voor geen schema");
                if (text !== null) this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: text.split(",").map(Number)})
            } else if (td.classList.contains("input-hour-min")) {
                let text = prompt("Geef uur en minuut in formaat HH:MM");
                if (text !== null) {
                    try {
                        let [h, m] = text.split(":");
                        h = parseInt(h);
                        m = parseInt(m);
                        if (h >= 0 && h < 24 && m >= 0 && m < 60)
                            this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: text})
                        else
                            this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: ""})
                    } catch (e) {
                        this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: ""})
                    }
                }
            } else if (td.classList.contains("off-on-auto") || td.classList.contains("yellow-gray-auto-man"))
                this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: td.textContent})

        })
    }

    set_cell_content_bg(td, value) {
        if (td.classList.contains("off-on-auto")) {
            td.textContent = String(value);
            if (value === "AUTO") {
                td.classList.remove("red-bg", "green-bg");
                td.classList.add("orange-bg");
            }
        } else if (td.classList.contains("green-red-aan-uit")) {
            td.textContent = value ? "AAN" : "UIT";
            td.classList.remove(value ? "red-bg" : "green-bg");
            td.classList.add(value ? "green-bg" : "red-bg");
        } else if (td.classList.contains("yellow-gray-auto-man")) {
            td.textContent = String(value);
            td.classList.remove("yellow-bg", "gray-bg");
            td.classList.add(value === "AUTO" ? "yellow-bg" : "gray-bg");
        } else if (td.classList.contains("green-white")) {
            td.textContent = value ? "AAN" : "UIT";
            td.classList.remove(value ? "white-bg-fg" : "green-bg-fg");
            td.classList.add(value ? "green-bg-fg" : "white-bg-fg");
        } else
            td.textContent = String(value);
    }

    // event: misc event
    // type: what needs to be done when the event is received
    // row: apply on what row
    subscribe_misc_cell_update(event, type, row) {
        this.misc_cell_updates[event] = {type, row};
    }

    misc_cell_update(row, id, type, value) {
        const td = document.querySelector(`[data-${this.table_data.data_label}="${row}-${id}"]`);
        if (!td) return;
        if (type === "red-green-bg") {
            td.classList.remove("red-bg", "green-bg", "orange-bg");
            td.classList.add(value ? "green-bg" : "red-bg");
        } else if (type === "text") {
            td.textContent = String(value);
        }
    }
}

class SonoffTable extends TableBase {
    constructor(table, rows) {
        const table_data = {
            labels: ["id", "loc", "status", "mode", "ip", "schema"],
            properties: ["sonoff_id", "location", "active", "mode", "ip", "schemes"],
            types: ["input-sonoff-id", "input-locatie", "green-red-aan-uit", "yellow-gray-auto-man", "", "input-schema"],
            data: rows,
            html_table: table,
            data_label: "sonoff_id",
            sio_namespace: "sonoffupdate",
        }
        super(table_data);
        this.subscribe_misc_cell_update("sonoffstate", "red-green-bg", "active")

        const mobile = window.matchMedia("(max-width: 767px)");
        const body = table.tBodies[0];
        const labels = Array.from(body.rows, row => row.cells[0]);
        const transpose = () => {
            const rows = Array.from(body.rows);
            const transposed = Array.from(rows[0].cells, () => document.createElement("tr"));
            for (const row of rows) {
                Array.from(row.cells).forEach((cell, index) => transposed[index].append(cell));
            }
            body.replaceChildren(...transposed);
            for (const label of labels) label.setAttribute("role", mobile.matches ? "columnheader" : "rowheader");
        };
        if (mobile.matches) {
            transpose();
        } else {
            for (const label of labels) label.setAttribute("role", "rowheader");
        }
        mobile.addEventListener("change", transpose);
        this.setupDeviceMenu(table);
    }

    setupDeviceMenu(table) {
        const menu = document.querySelector("#device-actions");
        const select = document.querySelector("#device-to-delete");
        const deleteButton = document.querySelector("#delete-device");
        let pending = false;

        const selectDevice = (id = "") => {
            select.replaceChildren(new Option("Kies een apparaat", ""));
            for (const cell of table.querySelectorAll(".input-sonoff-id")) {
                const deviceId = cell.dataset.sonoff_id.split("-")[1];
                const option = new Option(cell.textContent || `Lege plek (${deviceId})`, deviceId);
                option.dataset.sonoffId = cell.textContent;
                select.add(option);
            }
            select.value = id;
            deleteButton.disabled = !select.value;
        };

        document.querySelector("#device-actions-button").addEventListener("click", () => {
            menu.style.removeProperty("inset");
            menu.style.removeProperty("margin");
            selectDevice();
        });
        table.addEventListener("contextmenu", event => {
            const cell = event.target.closest("td[data-sonoff_id]");
            selectDevice(cell?.dataset.sonoff_id.split("-")[1]);
            openContextMenu(menu, event);
        });
        select.addEventListener("change", () => { deleteButton.disabled = !select.value; });

        const save = async (method, data) => {
            if (pending) return;
            pending = true;
            try {
                const response = await fetch(menu.dataset.url, {method, headers: {"Content-Type": "application/json"}, body: JSON.stringify(data)});
                if (!response.ok) {
                    const {error} = await response.json();
                    alert(error);
                    return;
                }
                window.location.reload();
            } catch {
                alert("Opslaan mislukt. Probeer het opnieuw.");
            } finally {
                pending = false;
            }
        };
        document.querySelector("#add-device").addEventListener("click", () => {
            const sonoffId = prompt("Geef een Sonoff-id (bijvoorbeeld sonoff21)")?.trim();
            if (sonoffId) save("POST", {sonoff_id: sonoffId});
        });
        deleteButton.addEventListener("click", () => {
            const option = select.selectedOptions[0];
            if (option?.value && confirm(`${option.textContent} verwijderen?`)) {
                save("DELETE", {id: Number(option.value), sonoff_id: option.dataset.sonoffId});
            }
        });
    }
}

class SchemeTable extends TableBase {
    constructor(table, rows) {
        const table_data = {
            labels: ["act", "ma", "di", "wo", "do", "vr", "za", "zo", "aan", "uit", "aan", "uit"],
            properties: ["active", "mon", "tue", "wed", "thu", "fri", "sat", "sun", "on0", "off0", "on1", "off1"],
            types: ["green-red-aan-uit", "green-white", "green-white", "green-white", "green-white", "green-white", "green-white", "green-white", "input-hour-min", "input-hour-min", "input-hour-min", "input-hour-min"],
            data: rows,
            html_table: table,
            data_label: "scheme_id",
            sio_namespace: "schemeupdate",
            header: "<tr><th>schema</th><th colspan='2'>1</th><th colspan='2'>2</th><th colspan='2'>3</th><th colspan='2'>4</th> </tr>"
        }
        super(table_data);
    }
}


