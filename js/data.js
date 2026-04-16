const API_URL = 'https://script.google.com/macros/s/AKfycbwcdITy_-UPkY4n8hEPER9hy-NMSH1Ky3kksEoubeeREiMcH13bThPVTWWsvudc15rHPg/exec';

async function loadMLBData() {
  const container = document.getElementById('stats-grid');
  
  try {
    const response = await fetch(API_URL);
    const players = await response.json();

    // Clear the loading message
    container.innerHTML = '';

    players.forEach(player => {
      // Hide the "Inactive" noise (-100 floor)
      if (player.PPV !== -100) {
        const card = `
          <div style="border: 1px solid #ddd; padding: 15px; margin: 10px; border-radius: 8px; background: white; color: #333; font-family: sans-serif; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="margin: 0; color: #1a1a1a;">${player.Player || 'Unknown'}</h3>
            <p style="margin: 5px 0;">Points: <strong>${player.Points}</strong> | ABs: <strong>${player.ABs}</strong></p>
            <p style="margin: 5px 0;">PPV: <span style="color: #007bff; font-weight: bold;">${Number(player.PPV).toFixed(3)}</span></p>
          </div>
        `;
        container.innerHTML += card;
      }
    });
  } catch (error) {
    container.innerHTML = '<p>Error loading data. Check back soon!</p>';
    console.error(error);
  }
}

loadMLBData();
