
// SAFE CHART HELPER
function createBarChart(id, labels, data, color, title) {
    new Chart(document.getElementById(id), {
        type: "bar",
        data: {
            labels: labels.length ? labels : ["No Data"],
            datasets: [{
                label: title,
                data: data.length ? data : [0],
                backgroundColor: color
            }]
        }
    });
}


function createPieChart(id, fake, real) {
    new Chart(document.getElementById(id), {
        type: "pie",
        data: {
            labels: ["Fake", "Genuine"],
            datasets: [{
                data: [fake, real],
                backgroundColor: ["#f5576c", "#43e97b"]
            }]
        }
    });
}
