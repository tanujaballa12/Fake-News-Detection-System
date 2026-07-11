// ===============================
// SELECT HTML ELEMENTS
// ===============================

const newsText = document.getElementById("news");
const predictBtn = document.getElementById("predictBtn");
const clearBtn = document.getElementById("clearBtn");
const loading = document.getElementById("loading");
const result = document.getElementById("result");
const count = document.getElementById("count");

// ===============================
// CHARACTER COUNTER
// ===============================

if (newsText && count) {
    newsText.addEventListener("input", () => {
        count.innerText = newsText.value.length;
    });
}

// ===============================
// CLEAR BUTTON
// ===============================

if (clearBtn) {
    clearBtn.addEventListener("click", () => {

        newsText.value = "";
        count.innerText = "0";
        result.innerHTML = "";
        loading.style.display = "none";

    });
}

// ===============================
// DARK MODE
// ===============================

const darkMode = document.getElementById("darkMode");

if (darkMode) {
    darkMode.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");
    });
}

// ===============================
// PREDICT BUTTON
// ===============================

if (predictBtn) {

    predictBtn.addEventListener("click", async () => {

        const text = newsText.value.trim();

        if (text === "") {
            alert("Please paste some news.");
            return;
        }

        loading.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary"></div>
            <h5 class="mt-3">AI is analyzing your news...</h5>
        </div>
        `;

        loading.style.display = "block";
        result.innerHTML = "";

        try {

            const response = await fetch("/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    news: text
                })
            });

            const data = await response.json();

            loading.style.display = "none";

            let color = data.prediction === "Fake" ? "red" : "green";

            result.innerHTML = `
            <div class="card shadow-lg border-0 mt-4">

                <div class="card-header ${data.prediction === "Real" ? "bg-success" : "bg-danger"} text-white">
                    <h3 class="mb-0">
                        <i class="fa-solid ${data.prediction === "Real" ? "fa-circle-check" : "fa-circle-xmark"}"></i>
                        Prediction Result
                    </h3>
                </div>

                <div class="card-body text-center">

                    <h2 style="color:${color}; font-weight:bold;">
                        ${data.prediction} News
                    </h2>

                    <p class="fs-5">Confidence Score</p>

                    <div class="progress mb-3" style="height:25px;">
                        <div
                            class="progress-bar ${data.prediction === "Real" ? "bg-success" : "bg-danger"}"
                            style="width:${data.confidence};">
                            ${data.confidence}
                        </div>
                    </div>

                    <table class="table table-bordered">

                        <tr>
                            <th>Model</th>
                            <td>Logistic Regression</td>
                        </tr>

                        <tr>
                            <th>Vectorizer</th>
                            <td>TF-IDF</td>
                        </tr>

                        <tr>
                            <th>Status</th>
                            <td>${data.prediction}</td>
                        </tr>

                        <tr>
                            <th>Date</th>
                            <td>${new Date().toLocaleString()}</td>
                        </tr>

                    </table>

                </div>

            </div>
            `;

            saveHistory(data.prediction, data.confidence);

        } catch (error) {

            loading.style.display = "none";

            result.innerHTML = `
            <div class="alert alert-danger">
                Error connecting Flask server.
            </div>
            `;

            console.error(error);
        }

    });

}

// ===============================
// SAVE HISTORY
// ===============================

function saveHistory(prediction, confidence) {

    let history = JSON.parse(localStorage.getItem("history")) || [];

    history.push({
        prediction,
        confidence,
        date: new Date().toLocaleString()
    });

    localStorage.setItem("history", JSON.stringify(history));

    loadHistory();
}

// ===============================
// LOAD HISTORY
// ===============================

function loadHistory() {

    let history = JSON.parse(localStorage.getItem("history")) || [];

    let table = document.getElementById("historyTable");

    if (!table) return;

    table.innerHTML = "";

    history.forEach((item, index) => {

        table.innerHTML += `
        <tr>
            <td>${index + 1}</td>
            <td>${item.prediction}</td>
            <td>${item.confidence}</td>
            <td>${item.date}</td>
        </tr>
        `;

    });

}

loadHistory();

// ===============================
// CLEAR HISTORY
// ===============================

const clearHistoryBtn = document.getElementById("clearHistory");

if (clearHistoryBtn) {

    clearHistoryBtn.addEventListener("click", () => {

        localStorage.removeItem("history");

        loadHistory();

    });

}

// ===============================
// DOWNLOAD CSV
// ===============================

const downloadBtn = document.getElementById("downloadCSV");

if (downloadBtn) {

    downloadBtn.addEventListener("click", () => {

        let history = JSON.parse(localStorage.getItem("history")) || [];

        let csv = "Prediction,Confidence,Date\n";

        history.forEach(item => {
            csv += `${item.prediction},${item.confidence},${item.date}\n`;
        });

        let blob = new Blob([csv], { type: "text/csv" });

        let url = URL.createObjectURL(blob);

        let a = document.createElement("a");

        a.href = url;
        a.download = "prediction_history.csv";

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

    });

}

// ===============================
// RESET BUTTON
// ===============================

const resetBtn = document.getElementById("resetBtn");

if (resetBtn) {

    resetBtn.addEventListener("click", () => {

        newsText.value = "";
        count.innerText = "0";
        result.innerHTML = "";
        loading.style.display = "none";

    });

}
