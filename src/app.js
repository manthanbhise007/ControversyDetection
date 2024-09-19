async function analyzeControversy() {
    const text = document.getElementById('inputText').value;
    const response = await fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
    });
    const result = await response.json();
    displayResults(result);
}

function displayResults(result) {
    const resultsDiv = document.getElementById('results');
    if (result.controversy_detected) {
        resultsDiv.innerHTML = `<p>Controversy Detected: ${result.details}</p>`;
    } else {
        resultsDiv.innerHTML = '<p>No Controversy Detected</p>';
    }
}
