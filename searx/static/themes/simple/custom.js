document.addEventListener('DOMContentLoaded', function() {
    var audios = document.querySelectorAll('.audio-control-psql audio');

    audios.forEach(function(audio) {
        audio.addEventListener('play', function() {
            pauseOtherAudios(audio);
            audio.parentNode.style.border = '2px solid limegreen';
        });

        audio.addEventListener('ended', function() {
            resetBorders();
        });
    });

    function resetBorders() {
        audios.forEach(function(audio) {
            audio.parentNode.style.border = '1px solid lightgrey'; // Set the desired default border color
        });
    }

    function pauseOtherAudios(currentAudio) {
        audios.forEach(function(audio) {
            if (audio !== currentAudio) {               
                if (!audio.paused) {
                    audio.parentNode.style.border = '1px solid darkred';
                }
            audio.pause();
            }
        });
    }
});