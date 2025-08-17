                let seconds = parseInt(document.getElementById('countdown').textContent);
                let countdown = document.getElementById('countdown');
                let interval = setInterval(function() {
                    seconds--;
                    if (seconds <= 0) {
                        clearInterval(interval);
                        window.location.reload();
                    } else {
                        countdown.textContent = seconds;
                    }
                }, 1000);
        