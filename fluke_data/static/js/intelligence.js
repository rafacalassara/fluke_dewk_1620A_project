function populateCard(data) {
    document.getElementById('title').innerText = data.title;
    document.getElementById('summary').innerText = data.summary;
    document.getElementById('analytics').innerText = data.analytics;
    document.getElementById('suggestion').innerText = data.suggestion;
    document.getElementById('conclusion').innerText = data.conclusion;
}

function setLoading(state) {
    try {
        document.getElementById('dataCard').style.display = !state ? 'none' : 'block'; 
        document.getElementById('skeletonCard').style.display = !state ? 'block' : 'none'; 
    }catch (e) {};
}

async function fetchData() {
    try {
        const response = await fetch('/api/analyze-with-ai/'); // URL fictícia
        const data = await response.json();
        
        populateCard(data);

        setLoading(true);
    } catch (error) {
        console.error('Erro ao buscar dados:', error);
    }
}

document.addEventListener('DOMContentLoaded', async function() {
    setLoading();
    fetchData();
});
