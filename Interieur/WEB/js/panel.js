// Gestion du mode sombre
const darkModeBtn = document.getElementById('darkModeBtn');
const body = document.body;

darkModeBtn.addEventListener('click', () => {
	body.classList.toggle('dark-mode');
	if (body.classList.contains('dark-mode')) {
		darkModeBtn.innerHTML = '<i class="fa-solid fa-sun"></i> Mode Clair';
	} else {
		darkModeBtn.innerHTML = '<i class="fa-solid fa-moon"></i> Mode Sombre';
	}
});

// Fonction pour récupérer les valeurs de l'API et les mettre dans les inputs
async function loadAlertValues() {
	try {
		const response = await fetch('/api/check_alert');
		if (!response.ok) {
			throw new Error('Erreur HTTP ' + response.status);
		}
		const data = await response.json();

		document.getElementById('temp_min').value = data.temp_min ?? '';
		document.getElementById('temp_max').value = data.temp_max ?? '';
		document.getElementById('humidity_min').value = data.humidity_min ?? '';
		document.getElementById('humidity_max').value = data.humidity_max ?? '';
	} catch (error) {
		console.error('Erreur en récupérant les valeurs des alertes :', error);
	}
}

// Charger les valeurs au chargement de la page
window.addEventListener('DOMContentLoaded', loadAlertValues);

// Gestion du formulaire d'alerte
const alertForm = document.getElementById('alertForm');
alertForm.addEventListener('submit', async (e) => {
	e.preventDefault();

	const temp_min = parseFloat(document.getElementById('temp_min').value);
	const temp_max = parseFloat(document.getElementById('temp_max').value);
	const humidity_min = parseFloat(document.getElementById('humidity_min').value);
	const humidity_max = parseFloat(document.getElementById('humidity_max').value);

	if (isNaN(temp_min) || isNaN(temp_max) || isNaN(humidity_min) || isNaN(humidity_max)) {
		alert("Veuillez remplir tous les champs correctement.");
		return;
	}

	const data = {
		temp_min,
		temp_max,
		humidity_min,
		humidity_max
	};

	try {
		const response = await fetch('/save-alert-config', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(data),
		});

		if (!response.ok) {
			throw new Error('Erreur réseau');
		}

		const result = await response.json();
		alert('Configuration sauvegardée !');
		await loadAlertValues(); // recharge les valeurs depuis l'API
	} catch (err) {
		console.error(err);
		alert('Erreur lors de la sauvegarde.');
	}
});