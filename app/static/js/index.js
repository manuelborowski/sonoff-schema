window.addEventListener('DOMContentLoaded', (event) => {
    const sonoff_table = new SonoffTable(document.querySelector(".sonoff-table"));
    const scheme_table = new SchemeTable(document.querySelector(".scheme-table"));
});


class TableBase {
    constructor(table_data) {
        // Create and populate table
        for (var i = 0; i < table_data.labels.length; i++) table_data.labels[i] = `<td>${table_data.labels[i]}</td>`
        for (var i = 0; i < table_data.data.length; i++) {
            for (var j = 0; j < table_data.properties.length; j++) {
                table_data.labels[j] += `<td class="${table_data.types[j]}" data-${table_data.data_label}="${table_data.properties[j]}-${table_data.data[i].id}">${table_data.data[i][table_data.properties[j]]}</td>`;
            }
        }
        var table_content = "";
        for (var i = 0; i < table_data.labels.length; i++) table_content += `<tr>${table_data.labels[i]}</tr>`;
        table_data.html_table.innerHTML = table_content
        for (var y = 0; y < table_data.html_table.rows.length; y++) {
            for (var x = 0; x < table_data.html_table.rows[y].cells.length; x++) {
                const td = table_data.html_table.rows[y].cells[x];
                if (td.classList.contains("green-white") || td.classList.contains("green-red-aan-uit"))
                    this.set_cell_content_bg(td, td.innerHTML === "true")
                else
                    this.set_cell_content_bg(td, td.innerHTML)
            }
        }

        this.table_data = table_data;
        this.socket = io("/" + table_data.sio_namespace);
        this.extra_cell_updates = {}

        // Receive table update events from server
        this.socket.on("json", (data) => {
            const td = document.querySelector(`[data-${this.table_data.data_label}="${data.id}"]`);
            if (td)
                this.set_cell_content_bg(td, data.value);
            else if (this.extra_cell_updates) {
                const [event, id] = data.id.split("-");
                if (this.extra_cell_updates[event]) {
                    this.set_cell_update(this.extra_cell_updates[event].row, id, this.extra_cell_updates[event].type, data.value);
                }
            }
        });
        // Send table update events to server
        table_data.html_table.addEventListener("click", e => {
            const td = e.target;
            if (td.classList.contains("green-white") || td.classList.contains("green-red-aan-uit")) {
                this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: td.innerHTML === "AAN"})
            } else if (td.classList.contains("input-locatie")) {
                let text = prompt("Geef een locatie");
                this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: text})
            } else if (td.classList.contains("input-schema")) {
                let text = prompt("Geef één of meerdere locaties, gescheiden door een komma");
                this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: text.split(",").map(Number)})
            } else if (td.classList.contains("input-hour-min")) {
                let text = prompt("Geef uur en minuut in formaat HH:MM");
                try {
                    let [h, m] = text.split(":");
                    h = parseInt(h);
                    m = parseInt(m);
                    if (h >= 0 && h < 24 && m >= 0 && m < 60)
                        this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: text})
                    else
                        alert("Verkeerd formaat, probeer nogmaals")
                } catch (e) {
                    alert("Verkeerd formaat, probeer nogmaals")
                }
            } else
                this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: td.innerHTML})

        })
    }

    set_cell_content_bg(td, value) {
        if (td.classList.contains("off-on-auto")) {
            td.innerHTML = value;
            if (value === "AUTO") {
                td.classList.remove("red-bg", "green-bg");
                td.classList.add("orange-bg");
            }
        } else if (td.classList.contains("green-red-aan-uit")) {
            td.innerHTML = value ? "AAN" : "UIT";
            td.classList.remove(value ? "red-bg" : "green-bg");
            td.classList.add(value ? "green-bg" : "red-bg");
        } else if (td.classList.contains("green-white")) {
            td.innerHTML = value ? "AAN" : "UIT";
            td.classList.remove(value ? "white-bg-fg" : "green-bg-fg");
            td.classList.add(value ? "green-bg-fg" : "white-bg-fg");
        } else
            td.innerHTML = value;
    }

    // event: arbitrary event
    // type: what needs to be done when the event is received
    // row: apply on what row
    subscribe_cell_update(event, type, row) {
        this.extra_cell_updates[event] = {type, row};
    }

    set_cell_update(row, id, type, value) {
        const td = document.querySelector(`[data-${this.table_data.data_label}="${row}-${id}"]`);
        console.log(td, id, type, value)
        if(type === "red-green-bg") {
            td.classList.remove("red-bg", "green-bg", "orange-bg");
            td.classList.add(value ? "green-bg" : "red-bg");
        }

    }

}

class SonoffTable extends TableBase {
    constructor(table) {
        const table_data = {
            labels: ["id", "loc", "mode", "ip", "schema"],
            properties: ["sonoff_id", "location", "mode", "ip", "schemes"],
            types: ["", "input-locatie", "off-on-auto", "", "input-schema"],
            data: sonoffs,
            html_table: table,
            data_label: "sonoff_id",
            sio_namespace: "sonoffupdate",
        }
        super(table_data);

        this.subscribe_cell_update("sonoffstate", "red-green-bg", "mode")
    }
}

class SchemeTable extends TableBase {
    constructor(table) {
        const table_data = {
            labels: ["act", "ma", "di", "wo", "do", "vr", "za", "zo", "aan", "uit", "aan", "uit"],
            properties: ["active", "mon", "tue", "wed", "thu", "fri", "sat", "sun", "on0", "off0", "on1", "off1"],
            types: ["green-red-aan-uit", "green-white", "green-white", "green-white", "green-white", "green-white", "green-white", "green-white", "input-hour-min", "input-hour-min", "input-hour-min", "input-hour-min"],
            data: schemes,
            html_table: table,
            data_label: "scheme_id",
            sio_namespace: "schemeupdate"
        }
        super(table_data);
    }
}


