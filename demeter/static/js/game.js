// Oyun sayfası için JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Oyun durumunu tutan nesne
    const gameState = {
    resources: {
        energy: 100,        // Enerji
        water: 100,         // Saflaştırılmış su
        nutrients: 50,      // Toprak besleyicileri/gübre
        oxygen: 100,        // Oksijen
        food: 50,           // Besin ürünleri
        recycledMatter: 20, // Geri dönüştürülmüş atık
        scientificData: 0,  // Bilimsel veri puanları
        robotParts: 10      // Robot yedek parçaları
    },
    crew: {
        morale: 80,         // Mürettebat morali
        effortPoints: 100,  // Günlük efor puanları
        skills: {
            farming: 1,     // Tarım becerisi
            engineering: 1, // Mühendislik becerisi
            science: 1      // Bilim becerisi
        }
    },
    selectedCrop: null,
    modules: [],
    level: 1,
    day: 1,                // Oyun günü
    maxModules: 9,
    unlockedSeeds: [],     // Açılmış tohumları tutacak dizi
    seedInventory: {}      // Tohum envanteri
};

    // Ekin türleri ve özellikleri (dinamik olarak doldurulacak)
    let cropTypes = {};

    // UI Elemanları
    const farmModulesContainer = document.getElementById('farm-modules');
    const addModuleButton = document.getElementById('add-module');
    const upgradeButton = document.getElementById('upgrade-system');
    const statusReport = document.getElementById('status-report');
    const notificationArea = document.getElementById('notification-area');

    // Crop butonlarını oluşturacak fonksiyon
    function createCropButtons() {
        const cropSelectionContainer = document.querySelector('.crop-selection');
        cropSelectionContainer.innerHTML = ''; // Mevcut butonları temizle

        // Her açılmış tohum için buton oluştur
        Object.keys(cropTypes).forEach(cropId => {
            const crop = cropTypes[cropId];
            const button = document.createElement('button');
            button.classList.add('crop-btn');
            button.setAttribute('data-crop', cropId);
            button.innerHTML = `${crop.icon} ${crop.name}`;

            button.addEventListener('click', function() {
                gameState.selectedCrop = cropId;

                // Seçili düğmeyi vurgula
                document.querySelectorAll('.crop-btn').forEach(btn => btn.classList.remove('selected'));
                this.classList.add('selected');

                showNotification(`${crop.name} seçildi. Ekmek için bir modüle tıklayın.`);
            });

            cropSelectionContainer.appendChild(button);
        });
    }

    // Tohumları API'den çek
    function fetchSeeds() {
        fetch('/api/seeds')
            .then(response => response.json())
            .then(data => {
                // Açılmış tohumları kaydet
                gameState.unlockedSeeds = data.map(seed => seed.id);

                // cropTypes nesnesini doldur
                data.forEach(seed => {
                    cropTypes[seed.id] = {
                        name: seed.common_name,
                        icon: seed.icon,
                        growthTime: seed.growth_time, // Artık doğrudan saniye cinsinden
                        waterUsage: seed.water_req,
                        oxygenProduction: seed.oxygen_production,
                        foodProduction: seed.biomass_production,
                        energyUsage: seed.nutrient_req
                    };
                });

                // Tohum butonlarını oluştur
                createCropButtons();

                // Oyunu başlat
                initGame();
            })
            .catch(error => {
                console.error('Tohumlar yüklenemedi:', error);
                showNotification('Tohumlar yüklenemedi!', 'error');

                // Hata durumunda varsayılan tohumlarla devam et
                const defaultSeeds = {
                    'default_seed': {
                        name: 'Varsayılan Tohum',
                        icon: '🌱',
                        growthTime: 60,
                        waterUsage: 2,
                        oxygenProduction: 1,
                        foodProduction: 3,
                        energyUsage: 1
                    }
                };

                cropTypes = defaultSeeds;
                createCropButtons();
                initGame();
            });
    }

    // Modül ekleme
    addModuleButton.addEventListener('click', function() {
        if (gameState.modules.length < gameState.maxModules) {
            gameState.modules.push({
                id: Date.now(),
                crop: null,
                plantedAt: null,
                growthStage: 0
            });
            renderFarmModules();
            showNotification('Yeni tarım modülü eklendi!');
        } else {
            showNotification('Maksimum modül sayısına ulaştınız. Seviye atlayarak daha fazla modül ekleyebilirsiniz.', 'warning');
        }
    });

    // Sistem yükseltme
    upgradeButton.addEventListener('click', function() {
        if (gameState.resources.energy >= 50) {
            gameState.resources.energy -= 50;
            gameState.level += 1;
            gameState.maxModules += 3;
            updateResourceDisplay();
            document.getElementById('level').textContent = gameState.level;
            showNotification('Sistemler yükseltildi! Yeni modüller açıldı.', 'success');
        } else {
            showNotification('Yükseltme için yeterli enerji yok!', 'error');
        }
    });

    // Ekin ekme fonksiyonu
    function plantCrop(moduleId, cropId) {
        // Yeterli kaynak var mı kontrol et
        if (gameState.resources.water < 10) {
            showNotification('Ekin ekmek için yeterli su yok!', 'error');
            return;
        }

        if (gameState.resources.energy < 5) {
            showNotification('Ekin ekmek için yeterli enerji yok!', 'error');
            return;
        }

        // Modülü bul ve güncelle
        const moduleIndex = gameState.modules.findIndex(m => m.id === moduleId);
        if (moduleIndex !== -1) {
            gameState.modules[moduleIndex].crop = cropId;
            gameState.modules[moduleIndex].plantedAt = Date.now();
            gameState.modules[moduleIndex].growthStage = 0;

            // Kaynakları güncelle
            gameState.resources.water -= 10;
            gameState.resources.energy -= 5;
            updateResourceDisplay();

            renderFarmModules();
            showNotification(`${cropTypes[cropId].name} ekildi!`);

            // Sunucuya bildir
            sendPlantCropToServer(moduleId, cropId);
        }
    }

    // Ekin hasat etme fonksiyonu
    function harvestCrop(module) {
        const crop = cropTypes[module.crop];

        // Kaynakları güncelle
        gameState.resources.food += crop.foodProduction;
        gameState.resources.oxygen += crop.oxygenProduction;
        updateResourceDisplay();

        // Modülü temizle
        const moduleIndex = gameState.modules.findIndex(m => m.id === module.id);
        if (moduleIndex !== -1) {
            gameState.modules[moduleIndex].crop = null;
            gameState.modules[moduleIndex].plantedAt = null;
            gameState.modules[moduleIndex].growthStage = 0;
        }

        renderFarmModules();
        showNotification(`${crop.name} hasat edildi! +${crop.foodProduction} Yiyecek, +${crop.oxygenProduction} Oksijen`);
    }

    // Büyüme yüzdesini hesapla
    function calculateGrowthPercent(module) {
        if (!module.crop || !module.plantedAt) return 0;

        const crop = cropTypes[module.crop];
        const elapsedTime = (Date.now() - module.plantedAt) / 1000; // saniye cinsinden
        const growthPercent = Math.min(100, Math.floor((elapsedTime / crop.growthTime) * 100));

        return growthPercent;
    }

    // Kalan süreyi hesapla ve formatla
    function formatRemainingTime(module) {
        if (!module.crop || !module.plantedAt) return "";

        const crop = cropTypes[module.crop];
        const elapsedTime = (Date.now() - module.plantedAt) / 1000; // saniye cinsinden
        const remainingTime = Math.max(0, crop.growthTime - elapsedTime);

        if (remainingTime <= 0) return "Hasat edilebilir!";

        // Süreyi formatlayalım
        const days = Math.floor(remainingTime / 86400);
        const hours = Math.floor((remainingTime % 86400) / 3600);
        const minutes = Math.floor((remainingTime % 3600) / 60);
        const seconds = Math.floor(remainingTime % 60);

        let timeString = "";
        if (days > 0) timeString += `${days}g `;
        if (hours > 0 || days > 0) timeString += `${hours}s `;
        if (minutes > 0 || hours > 0 || days > 0) timeString += `${minutes}d `;
        timeString += `${seconds}sn`;

        return `Kalan: ${timeString}`;
    }

    // Tarım modüllerini oluştur
    function renderFarmModules() {
        farmModulesContainer.innerHTML = '';

        // Mevcut modülleri göster
        for (let i = 0; i < gameState.modules.length; i++) {
            const module = gameState.modules[i];
            const moduleElement = document.createElement('div');
            moduleElement.classList.add('farm-module');
            moduleElement.setAttribute('data-id', module.id);

            if (module.crop) {
                // Ekin ekilmiş modül
                const crop = cropTypes[module.crop];
                const growthPercent = calculateGrowthPercent(module);

                moduleElement.innerHTML = `
                    <div class="module-crop">${crop.icon}</div>
                    <div class="module-info">
                        <div>${crop.name}</div>
                        <div class="growth-bar">
                            <div class="growth-progress" style="width: ${growthPercent}%"></div>
                        </div>
                        <div>${growthPercent}% Büyüme</div>
                        <div class="remaining-time">${formatRemainingTime(module)}</div>
                    </div>
                `;

                // Hasat edilebilir mi?
                if (growthPercent >= 100) {
                    moduleElement.classList.add('harvestable');
                    moduleElement.addEventListener('click', () => harvestCrop(module));
                }
            } else {
                // Boş modül
                moduleElement.classList.add('module-empty');
                moduleElement.innerHTML = `
                    <div>Boş Modül</div>
                    <div>Ekin ekmek için tıklayın</div>
                `;

                // Ekin ekme olayı
                moduleElement.addEventListener('click', () => {
                    if (gameState.selectedCrop) {
                        plantCrop(module.id, gameState.selectedCrop);
                    } else {
                        showNotification('Önce bir ekin türü seçin!', 'warning');
                    }
                });
            }

            farmModulesContainer.appendChild(moduleElement);
        }

        // Boş slotları göster
        for (let i = gameState.modules.length; i < gameState.maxModules; i++) {
            const emptySlot = document.createElement('div');
            emptySlot.classList.add('farm-module', 'module-empty', 'locked');
            emptySlot.innerHTML = `
                <div>Kilitli Modül</div>
                <div>"Yeni Modül Ekle" düğmesini kullanın</div>
            `;
            farmModulesContainer.appendChild(emptySlot);
        }
    }

    // Kaynak göstergesini güncelle
    function updateResourceDisplay() {
    // Ana kaynaklar
    document.querySelector('#energy .resource-value').textContent = Math.floor(gameState.resources.energy);
    document.querySelector('#water .resource-value').textContent = Math.floor(gameState.resources.water);
    document.querySelector('#nutrients .resource-value').textContent = Math.floor(gameState.resources.nutrients);
    document.querySelector('#oxygen .resource-value').textContent = Math.floor(gameState.resources.oxygen);
    document.querySelector('#food .resource-value').textContent = Math.floor(gameState.resources.food);

    // İkincil kaynaklar
    document.querySelector('#recycled-matter .resource-value').textContent = Math.floor(gameState.resources.recycledMatter);
    document.querySelector('#scientific-data .resource-value').textContent = Math.floor(gameState.resources.scientificData);
    document.querySelector('#robot-parts .resource-value').textContent = Math.floor(gameState.resources.robotParts);

    // Mürettebat bilgileri
    document.querySelector('#morale .crew-value').textContent = Math.floor(gameState.crew.morale);
    document.querySelector('#effort-points .crew-value').textContent = Math.floor(gameState.crew.effortPoints);
    document.querySelector('#day-counter').textContent = gameState.day;
    }

    // Bildirim göster
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.classList.add('notification');
        notification.classList.add(type);
        notification.textContent = message;

        notificationArea.appendChild(notification);

        // 5 saniye sonra bildirim kaybolsun
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s forwards';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    }

    // Sunucuya ekin ekme bilgisini gönder
    function sendPlantCropToServer(moduleId, cropId) {
        fetch('/api/plant_crop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                crop_type: cropId,
                position: moduleId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                showNotification('Sunucu ile iletişim hatası!', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Sunucu ile iletişim hatası!', 'error');
        });
    }

    // Kaynakları sunucuya gönder
    function sendResourcesToServer() {
        fetch('/api/update_resources', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(gameState.resources)
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Kaynaklar güncellenemedi');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    // Oyun döngüsü
    function runGameLoop() {
        // Ekinleri büyüt ve kaynakları güncelle
        gameState.modules.forEach(module => {
            if (module.crop) {
                const crop = cropTypes[module.crop];

                // Su ve enerji tüketimi
                gameState.resources.water -= crop.waterUsage * 0.01;
                gameState.resources.energy -= crop.energyUsage * 0.01;

                // Büyüme tamamlandıysa oksijen ve yiyecek üretimi
                const growthPercent = calculateGrowthPercent(module);
                if (growthPercent >= 100) {
                    // Tam büyümüş bitkiler oksijen üretir
                    gameState.resources.oxygen += crop.oxygenProduction * 0.01;
                }
            }
        });

        // Kaynakları sınırla
        gameState.resources.water = Math.max(0, Math.min(100, gameState.resources.water));
        gameState.resources.oxygen = Math.max(0, Math.min(100, gameState.resources.oxygen));
        gameState.resources.food = Math.max(0, gameState.resources.food);
        gameState.resources.energy = Math.max(0, Math.min(100, gameState.resources.energy));

        // Arayüzü güncelle
        updateResourceDisplay();
        renderFarmModules();

        // Durum raporunu güncelle
        updateStatusReport();

        // Kritik kaynak uyarıları
        checkResourceWarnings();
    }

    // Durum raporunu güncelle
    function updateStatusReport() {
        let report = 'Sistem Durumu: ';

        if (gameState.resources.oxygen < 20) {
            report += 'KRİTİK! Oksijen seviyesi düşük! ';
        } else if (gameState.resources.water < 20) {
            report += 'UYARI! Su seviyesi düşük! ';
        } else if (gameState.resources.energy < 20) {
            report += 'DİKKAT! Enerji seviyesi düşük! ';
        } else {
            report += 'Tüm sistemler normal çalışıyor. ';
        }

        // Büyüyen ekinler hakkında bilgi
        const growingCrops = gameState.modules.filter(m => m.crop !== null);
        if (growingCrops.length > 0) {
            report += `${growingCrops.length} ekin büyüyor. `;
        } else {
            report += 'Hiç ekin ekilmemiş! ';
        }

        statusReport.textContent = report;
    }

    // Kaynak uyarılarını kontrol et
    function checkResourceWarnings() {
        if (gameState.resources.oxygen < 10) {
            showNotification('KRİTİK UYARI: Oksijen seviyesi çok düşük!', 'error');
        } else if (gameState.resources.water < 10) {
            showNotification('UYARI: Su seviyesi çok düşük!', 'warning');
        } else if (gameState.resources.energy < 10) {
            showNotification('DİKKAT: Enerji seviyesi çok düşük!', 'warning');
        }
    }

    // Oyunu başlat
    function initGame() {
        renderFarmModules();
        updateResourceDisplay();

        // İlk modülü ekle
        if (gameState.modules.length === 0) {
            gameState.modules.push({
                id: Date.now(),
                crop: null,
                plantedAt: null,
                growthStage: 0
            });
            renderFarmModules();
        }



        // Oyun döngüsünü başlat (her 1 saniyede bir)
        setInterval(runGameLoop, 1000);

        // Kaynakları sunucuya gönder (her 30 saniyede bir)
        setInterval(sendResourcesToServer, 30000);

        showNotification('Demeter Uzay Tarım Simülasyonu başlatıldı!');
    }

    // Günü ilerletme fonksiyonu
    function advanceDay() {
        // Sunucuya istek gönder
        fetch('/api/advance_day', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Oyun durumunu güncelle
                gameState.day = data.day;
                gameState.crew.effortPoints = 100;


                // Arayüzü güncelle
                updateResourceDisplay();
                showNotification(data.message, "success");

                // Günlük olayları tetikle
                triggerDailyEvents();
            } else {
                showNotification("Gün ilerletilemedi: " + data.message, "error");
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification("Sunucu ile iletişim hatası!", "error");
        });
    }
    // Günlük olayları tetikleme
    function triggerDailyEvents() {
        // Temel kaynak tüketimi
        gameState.resources.oxygen -= 5;
        gameState.resources.water -= 5;
        gameState.resources.food -= 5;
        gameState.resources.energy -= 5;

        // Moral etkisi
        updateMorale();

        // Rastgele olaylar (şimdilik boş)

        // Kaynakları güncelle
        updateResourceDisplay();

        // Sunucuya kaydet
        sendResourcesToServer();
        sendCrewToServer();
    }
    // Moral güncelleme
    function updateMorale() {
        // Kaynak durumuna göre moral etkisi
        if (gameState.resources.food < 10 || gameState.resources.oxygen < 10) {
            gameState.crew.morale -= 10;
            showNotification("Kritik kaynak eksikliği morali düşürdü!", "warning");
        } else if (gameState.resources.food > 80 && gameState.resources.oxygen > 80) {
            gameState.crew.morale += 5;
            showNotification("Bol kaynaklar morali yükseltti!", "success");
        }

        // Moral sınırları
        gameState.crew.morale = Math.max(0, Math.min(100, gameState.crew.morale));
    }

    // Mürettebat verilerini sunucuya gönder
    function sendCrewToServer() {
        fetch('/api/update_crew', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(gameState.crew)
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Mürettebat verileri güncellenemedi');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    // Tohumları çek ve oyunu başlat
    fetchSeeds();
});

document.getElementById('advance-day').addEventListener('click', function() {
    advanceDay();
});
