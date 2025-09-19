document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('div.highlight-python').forEach(function(block) {
        if (block.querySelector('.copy-icon')) return; // avoid duplicates

        // Create SVG clipboard icon
        const ns = "http://www.w3.org/2000/svg";
        const svg = document.createElementNS(ns, "svg");
        svg.setAttribute("class", "copy-icon");
        svg.setAttribute("viewBox", "0 0 24 24");
        svg.innerHTML = '<path d="M16 1H4a2 2 0 0 0-2 2v14h2V3h12V1zm3 4H8a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2zm0 18H8V7h11v16z"/>';
        block.appendChild(svg);

        // Copy code to clipboard
        svg.addEventListener('click', function() {
            const code = block.querySelector('pre').innerText;
            navigator.clipboard.writeText(code).then(() => {
                // temporary feedback: icon color green
                svg.style.fill = "#a6e3a1";
                setTimeout(() => svg.style.fill = "#cba6f7", 1200);
            });
        });
    });
});
