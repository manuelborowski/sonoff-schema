window.addEventListener('DOMContentLoaded', (event) => {
    const sonoff_table = new SonoffTable(document.querySelector(".sonoff-table"));
    const scheme_table = new SchemeTable(document.querySelector(".scheme-table"));
});



class SonoffTable {
    constructor(table) {
        var labels = ["id", "loc", "act", "ip", "schema"]
        var properties = ["sonoff_id", "location", "active", "ip", "schemes"]
        var actions = ["", "input-locatie", "green-red-aan-uit", "", "input-schema"]
        for (var i = 0; i < labels.length; i++) labels[i] = `<td>${labels[i]}</td>`
        for (var i = 0; i < sonoffs.length; i++) {
            for (var j = 0; j < properties.length; j++) {
                labels[j] += `<td class="${actions[j]}" data-sonoff_id="${properties[j]}-${sonoffs[i].id}">${sonoffs[i][properties[j]]}</td>`;
            }
        }
        var table_content = "";
        for (var i = 0; i < labels.length; i++) table_content += `<tr>${labels[i]}</tr>`;
        table.innerHTML = table_content
        new Clickable(table, "sonoff_id", "sonoffstate");
    }
}

class SchemeTable {
    constructor(table) {
        var labels = ["act", "ma", "di", "wo", "do", "vr", "za", "zo", "aan", "uit", "aan", "uit"]
        var properties = ["active", "mon", "tue", "wed", "thu", "fri", "sat", "sun", "on0", "off0", "on1", "off1"]
        var actions = ["green-red-aan-uit", "green-white", "green-white", "green-white", "green-white", "green-white", "green-white", "green-white", "input-hour-min", "input-hour-min", "input-hour-min", "input-hour-min"]
        for (var i=0; i < labels.length; i++) labels[i] = `<td>${labels[i]}</td>`
        for (var i=0; i < schemes.length; i++) {
            for(var j=0; j < properties.length; j++) {
                labels[j] += `<td class="${actions[j]}" data-scheme_id="${properties[j]}-${schemes[i].id}">${schemes[i][properties[j]]}</td>`;
            }
        }
        var table_content = "<tr><th>nr</th><th colspan='2'>1</th><th colspan='2'>2</th><th colspan='2'>3</th><th colspan='2'>4</th></tr>";
        for(var i=0; i < labels.length; i++) table_content += `<tr>${labels[i]}</tr>`;
        table.innerHTML = table_content
        new Clickable(table, "scheme_id", "schemestate");
    }
}

class Clickable {
    constructor(table, data_label, io_namespace) {
        this.socket = io("/" + io_namespace);
        this.socket.on("json", (data) => {
            const td = document.querySelector(`[data-${this.data_label}="${data.id}"]`);
            if (td.classList.contains("green-red-aan-uit")) {
                this.set_green_red_aan_uit_state(td, data.value);
            }
            if (td.classList.contains("green-white")) {
                this.set_green_white_state(td, data.value);
            }
            if (td.classList.contains("input-locatie") || td.classList.contains("input-schema") || td.classList.contains("input-hour-min")) {
                this.set_input_text(td, data.value);
            }
        });
        this.data_label = data_label;
        table.addEventListener("click", e => {
            const td = e.target;
            if (td.classList.contains("green-red-aan-uit")) {
                this.socket.emit("json", {id: td.dataset[this.data_label], value: td.innerHTML !== "AAN"})
            }
            if (td.classList.contains("green-white")) {
                this.socket.emit("json", {id: td.dataset[this.data_label], value: td.innerHTML !== "true"})
            }
            if (td.classList.contains("input-locatie")) {
                let text = prompt("Geef een locatie");
                this.socket.emit("json", {id: td.dataset[this.data_label], value: text})
            }
            if (td.classList.contains("input-schema")) {
                 let text = prompt("Geef één of meerdere locaties, gescheiden door een komma");
                this.socket.emit("json", {id: td.dataset[this.data_label], value: text.split(",").map(Number)})
            }
            if (td.classList.contains("input-hour-min")) {
                 let text = prompt("Geef uur en minuut in formaat HH:MM");
                this.socket.emit("json", {id: td.dataset[this.data_label], value: text})
            }
        })

        for(var y=0; y < table.rows.length; y++) {
            for(var x=0; x < table.rows[y].cells.length; x++) {
                const cell = table.rows[y].cells[x];
                if (cell.classList.contains("green-red-aan-uit")) {
                    this.set_green_red_aan_uit_state(cell, cell.innerHTML === "true");
                }
                if (cell.classList.contains("green-white")) {
                    this.set_green_white_state(cell, cell.innerHTML === "true");
                }
            }
        }
    }

    set_green_red_aan_uit_state(td, state) {
        td.innerHTML = state ? "AAN" : "UIT";
        td.classList.remove(state ? "red-bg" : "green-bg");
        td.classList.add(state ? "green-bg" : "red-bg");
    }

    set_green_white_state(td, state) {
        td.innerHTML = state ? "true" : "false";
        td.classList.remove(state ? "white-bg-fg" : "green-bg-fg");
        td.classList.add(state ? "green-bg-fg" : "white-bg-fg");
    }

    set_input_text(td, value) {
        td.innerHTML = value
    }

}
