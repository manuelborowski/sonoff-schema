window.addEventListener('DOMContentLoaded', (event) => {
    const sonoff_table = new SonoffTable(document.querySelector(".sonoff-table"));
    const scheme_table = new SchemeTable(document.querySelector(".scheme-table"));
});


class TableBase {
    constructor(table_data) {
        for (var i = 0; i < table_data.labels.length; i++) table_data.labels[i] = `<td>${table_data.labels[i]}</td>`
        for (var i = 0; i < table_data.data.length; i++) {
            for (var j = 0; j < table_data.properties.length; j++) {
                table_data.labels[j] += `<td class="${table_data.types[j]}" data-${table_data.data_label}="${table_data.properties[j]}-${table_data.data[i].id}">${table_data.data[i][table_data.properties[j]]}</td>`;
            }
        }
        var table_content = "";
        for (var i = 0; i < table_data.labels.length; i++) table_content += `<tr>${table_data.labels[i]}</tr>`;
        table_data.html_table.innerHTML = table_content

        this.table_data = table_data;

        this.socket = io("/" + table_data.sio_namespace);
        this.socket.on("json", (data) => {
            const td = document.querySelector(`[data-${this.table_data.data_label}="${data.id}"]`);
            this.set_cell_content_bg(td, data.value);
        });
        table_data.html_table.addEventListener("click", e => {
            const td = e.target;
            if (td.classList.contains("green-white") || td.classList.contains("green-red-aan-uit")) {
                this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: td.innerHTML === "AAN"})
            }
            else if (td.classList.contains("input-locatie")) {
                let text = prompt("Geef een locatie");
                this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: text})
            }
            else if (td.classList.contains("input-schema")) {
                let text = prompt("Geef één of meerdere locaties, gescheiden door een komma");
                this.socket.emit("json", {id: td.dataset[this.table_data.data_label], value: text.split(",").map(Number)})
            }
            else if (td.classList.contains("input-hour-min")) {
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

        for (var y = 0; y < table_data.html_table.rows.length; y++) {
            for (var x = 0; x < table_data.html_table.rows[y].cells.length; x++) {
                const td = table_data.html_table.rows[y].cells[x];
                if (td.classList.contains("green-white") || td.classList.contains("green-red-aan-uit"))
                    this.set_cell_content_bg(td, td.innerHTML === "true")
                else
                    this.set_cell_content_bg(td, td.innerHTML)
            }
        }
    }

    set_cell_content_bg(td, value) {
        if (td.classList.contains("off-on-auto")) {
            // const add_bg_class = {"UIT": "red-bg", "AAN": "green-bg", "AUTO": "orange-bg"};
            // const bg_classes = ["red-bg", "green-bg", "orange-bg"];
            td.innerHTML = value;
            // for (let i = 0; i < bg_classes.length; i++) if (td.classList.contains(bg_classes[i])) td.classList.remove(bg_classes[i])
            // td.classList.add(add_bg_class[state]);
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
            sio_namespace: "sonoffstate"
        }
        super(table_data);
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
            sio_namespace: "schemestate"
        }
        super(table_data);
    }
}


