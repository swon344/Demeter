// Ana sayfa için JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Yıldız arka planı için ek yıldızlar oluştur
    createStars();

    // Başlat düğmesine animasyon ekle
    const startButton = document.querySelector('.start-button');
    if (startButton) {
        startButton.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 10px 25px rgba(80, 250, 123, 0.5)';
        });

        startButton.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 10px 20px rgba(80, 250, 123, 0.3)';
        });
    }
});

// Arka plan için ek yıldızlar oluştur
function createStars() {
    const starsContainer = document.querySelector('.stars');
    if (!starsContainer) return;

    for (let i = 0; i < 50; i++) {
        const star = document.createElement('div');
        star.classList.add('star');
        star.style.width = Math.random() * 3 + 'px';
        star.style.height = star.style.width;
        star.style.left = Math.random() * 100 + 'vw';
        star.style.top = Math.random() * 100 + 'vh';
        star.style.animationDelay = Math.random() * 5 + 's';
        starsContainer.appendChild(star);
    }
}