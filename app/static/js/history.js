const plot = document.querySelector("#history-plot");
if (plot) drawHistory(plot, JSON.parse(document.querySelector("#history-data").textContent));


function drawHistory(plot, history) {
    const svg = plot.querySelector("svg");
    const startTime = Date.parse(`${history.start}T00:00:00Z`);
    // The log records local wall-clock time. Use UTC arithmetic to preserve those clock readings on the phone.
    const dayFormat = new Intl.DateTimeFormat("nl-BE", {timeZone: "UTC", day: "2-digit", month: "2-digit"});
    const cursorFormat = new Intl.DateTimeFormat("nl-BE", {timeZone: "UTC", dateStyle: "short", timeStyle: "short"});
    const padding = 8;
    const axisHeight = 48;
    const laneHeight = 46;
    const height = axisHeight + history.devices.length * laneHeight;
    let width = 0;
    let cursorTime = null;
    let pointerId = null;
    let cursor, cursorLine, cursorLabel, cursorText;

    function add(parent, tag, attributes, content = "") {
        const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
        for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
        if (content) node.textContent = content;
        parent.append(node);
        return node;
    }

    function x(seconds) {
        return padding + (width - 2 * padding) * seconds / history.duration;
    }

    function render() {
        const nextWidth = Math.floor(plot.getBoundingClientRect().width);
        if (nextWidth <= 2 * padding || nextWidth === width) return;
        width = nextWidth;
        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
        svg.setAttribute("height", height);
        svg.replaceChildren();

        for (let day = 0; day <= 7; day++) {
            const seconds = day * 86400;
            const boundary = x(seconds);
            add(svg, "line", {x1: boundary, x2: boundary, y1: 20, y2: height, stroke: "#dee2e6"});
            if (day < 7) {
                add(svg, "text", {x: x(seconds + 43200), y: 14, "text-anchor": "middle"}, dayFormat.format(startTime + seconds * 1000));
            }
        }

        for (const [index, device] of history.devices.entries()) {
            const top = axisHeight + index * laneHeight;
            const color = `hsl(${index * 137.508 % 360} 72% 34%)`;
            const y = active => top + (active ? 21 : 37);
            const label = add(svg, "text", {x: padding + 4, y: top + 13, fill: color, "font-weight": "bold"}, device.device);
            add(label, "title", {}, device.device);
            add(svg, "line", {x1: padding, x2: width - padding, y1: top + laneHeight, y2: top + laneHeight, stroke: "#dee2e6"});
            let path = "";
            for (const [seconds, active] of device.events) {
                if (seconds > history.knownUntil) break;
                path += path ? ` H ${x(seconds)} V ${y(active)}` : `M ${x(seconds)} ${y(active)}`;
            }
            if (path) add(svg, "path", {d: `${path} H ${x(history.knownUntil)}`, fill: "none", stroke: color, "stroke-width": 2});
        }

        cursor = add(svg, "g", {"pointer-events": "none", visibility: "hidden"});
        cursorLine = add(cursor, "line", {y1: 20, y2: height, stroke: "#212529", "stroke-width": 1});
        cursorLabel = add(cursor, "rect", {y: 23, width: 132, height: 20, rx: 4, fill: "#212529"});
        cursorText = add(cursor, "text", {y: 37, fill: "white", "text-anchor": "middle"});
        updateCursor();
    }

    function updateCursor() {
        if (cursorTime === null) return;
        const position = x(cursorTime);
        const labelLeft = Math.max(padding, Math.min(position - 66, width - padding - 132));
        cursor.setAttribute("visibility", "visible");
        cursorLine.setAttribute("x1", position);
        cursorLine.setAttribute("x2", position);
        cursorLabel.setAttribute("x", labelLeft);
        cursorText.setAttribute("x", labelLeft + 66);
        cursorText.textContent = cursorFormat.format(startTime + cursorTime * 1000);
    }

    function moveCursor(event) {
        const bounds = svg.getBoundingClientRect();
        const position = (event.clientX - bounds.left) * width / bounds.width;
        const fraction = (position - padding) / (width - 2 * padding);
        cursorTime = Math.max(0, Math.min(history.duration - 1, fraction * history.duration));
        updateCursor();
    }

    svg.addEventListener("pointerdown", event => {
        if (!event.isPrimary || event.button !== 0 || !cursor) return;
        pointerId = event.pointerId;
        svg.setPointerCapture(pointerId);
        moveCursor(event);
    });
    svg.addEventListener("pointermove", event => {
        if (event.pointerId === pointerId) moveCursor(event);
    });
    svg.addEventListener("lostpointercapture", event => {
        if (event.pointerId === pointerId) pointerId = null;
    });

    new ResizeObserver(render).observe(plot);
    render();
}
