const form = document.getElementById('symptom-form');
const clearBtn = document.getElementById('clear-btn');
const resultsSection = document.getElementById('results');
const resultsList = document.getElementById('results-list');
const resultsNote = document.getElementById('results-note');
const errorEl = document.getElementById('error');
const searchBox = document.getElementById('symptom-search');
const grid = document.getElementById('symptom-grid');
const noMatches = document.getElementById('no-matches');
const selectedCount = document.getElementById('selected-count');
const chips = Array.from(grid.querySelectorAll('.chip'));

// Filter the (potentially large) symptom list as the user types
searchBox.addEventListener('input', () => {
  const q = searchBox.value.trim().toLowerCase();
  let visible = 0;
  chips.forEach((chip) => {
    const match = chip.dataset.label.includes(q);
    chip.style.display = match ? '' : 'none';
    if (match) visible += 1;
  });
  noMatches.classList.toggle('hidden', visible !== 0);
});

// Keep a running count of how many symptoms are checked, including ones
// currently hidden by the search filter
grid.addEventListener('change', updateSelectedCount);

function updateSelectedCount() {
  const n = form.querySelectorAll('input[name="symptoms"]:checked').length;
  selectedCount.textContent = n === 0 ? '' : `${n} selected`;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  errorEl.classList.add('hidden');

  const checked = Array.from(form.querySelectorAll('input[name="symptoms"]:checked'))
    .map(el => el.value);

  if (checked.length === 0) {
    showError('Select at least one symptom first.');
    return;
  }

  const submitBtn = document.getElementById('submit-btn');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Estimating…';

  try {
    const res = await fetch('/api/diagnose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symptoms: checked }),
    });
    const data = await res.json();

    if (!res.ok) {
      showError(data.error || 'Something went wrong.');
      return;
    }

    renderResults(data.results, data.symptom_count);
  } catch (err) {
    showError('Could not reach the server. Is the Flask app running?');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Estimate likely conditions';
  }
});

clearBtn.addEventListener('click', () => {
  form.reset();
  searchBox.value = '';
  chips.forEach((chip) => { chip.style.display = ''; });
  noMatches.classList.add('hidden');
  updateSelectedCount();
  resultsSection.classList.add('hidden');
  errorEl.classList.add('hidden');
});

function renderResults(results, symptomCount) {
  resultsList.innerHTML = '';
  const top = results.slice(0, 8);

  top.forEach((r) => {
    const li = document.createElement('li');
    li.className = 'result-row';
    li.innerHTML = `
      <div class="result-head">
        <span class="result-name">${r.disease}</span>
        <span class="result-pct">${r.certainty}%</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width:0%"></div>
      </div>
    `;
    resultsList.appendChild(li);
    requestAnimationFrame(() => {
      li.querySelector('.bar-fill').style.width = r.certainty + '%';
    });
  });

  resultsNote.textContent = `Based on ${symptomCount} symptom${symptomCount === 1 ? '' : 's'}. Highest-scoring conditions shown first.`;
  resultsSection.classList.remove('hidden');
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showError(msg) {
  errorEl.textContent = msg;
  errorEl.classList.remove('hidden');
}
