// --- WEB AUDIO API ARCADE SYNTHESIZER ---
let audioCtx = null;
function initAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
}
function playSound(type) {
    try {
        initAudio();
        if (!audioCtx || audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        
        const now = audioCtx.currentTime;
        
        if (type === 'click') {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(600, now);
            gain.gain.setValueAtTime(0.1, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.05);
            osc.start(now);
            osc.stop(now + 0.05);
        } 
        else if (type === 'plant') {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.type = 'sine';
            osc.frequency.setValueAtTime(250, now);
            osc.frequency.exponentialRampToValueAtTime(500, now + 0.15);
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
            osc.start(now);
            osc.stop(now + 0.15);
        }
        else if (type === 'harvest') {
            // Satisfying retro cash register sound (two fast beeps)
            const osc1 = audioCtx.createOscillator();
            const osc2 = audioCtx.createOscillator();
            const gain1 = audioCtx.createGain();
            const gain2 = audioCtx.createGain();
            
            osc1.connect(gain1); gain1.connect(audioCtx.destination);
            osc2.connect(gain2); gain2.connect(audioCtx.destination);
            
            osc1.type = 'square';
            osc1.frequency.setValueAtTime(880, now);
            gain1.gain.setValueAtTime(0.08, now);
            gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
            
            osc2.type = 'square';
            osc2.frequency.setValueAtTime(1200, now + 0.08);
            gain2.gain.setValueAtTime(0.08, now + 0.08);
            gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
            
            osc1.start(now); osc1.stop(now + 0.12);
            osc2.start(now + 0.08); osc2.stop(now + 0.25);
        }
        else if (type === 'levelUp') {
            // Rising arpeggio chord (major pentatonic)
            const notes = [261.63, 329.63, 392.00, 523.25, 659.25]; // C major notes
            notes.forEach((freq, idx) => {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(freq, now + (idx * 0.08));
                gain.gain.setValueAtTime(0.07, now + (idx * 0.08));
                gain.gain.exponentialRampToValueAtTime(0.001, now + (idx * 0.08) + 0.3);
                osc.start(now + (idx * 0.08));
                osc.stop(now + (idx * 0.08) + 0.35);
            });
        }
        else if (type === 'fail') {
            // Classic sliding down sad buzzer
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(220, now);
            osc.frequency.linearRampToValueAtTime(110, now + 0.35);
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.linearRampToValueAtTime(0.001, now + 0.35);
            osc.start(now);
            osc.stop(now + 0.4);
        }
        else if (type === 'prestige') {
            // Dramatic synth arpeggio cascade
            const chord = [293.66, 349.23, 440.00, 587.33, 698.46, 880.00]; // D minor
            for (let round = 0; round < 2; round++) {
                chord.forEach((freq, idx) => {
                    const osc = audioCtx.createOscillator();
                    const gain = audioCtx.createGain();
                    osc.connect(gain);
                    gain.connect(audioCtx.destination);
                    osc.type = 'sawtooth';
                    const delay = (round * 0.4) + (idx * 0.06);
                    osc.frequency.setValueAtTime(freq, now + delay);
                    gain.gain.setValueAtTime(0.08, now + delay);
                    gain.gain.exponentialRampToValueAtTime(0.001, now + delay + 0.25);
                    osc.start(now + delay);
                    osc.stop(now + delay + 0.3);
                });
            }
        }
    } catch (e) {
        console.error("Audio failed:", e);
    }
}
// --- GAME LOGIC & STATE ENGINE ---
let userStats = {
    username: 'Cargando...',
    gold: 0.0,
    prestige_count: 0,
    active_language: 'Python',
    porcentaje_auto: 0,
    auto_count: 0
};
let plots = [];
let selectedCrop = 'carrot'; // 'carrot', 'wheat', 'pumpkin'
let activeQuizPlot = null;
let activeQuizId = null;
// Hot Air Balloon and 3-Question Challenge variables
let balloonPlotIndex = null;
let balloonTip = null;
let activeChallengeStep = 0;
let activeChallengeTotal = 3;
let activeQuizData = null;
// SOW COST CONFIG
const SEED_COSTS = { 'carrot': 5.0, 'wheat': 15.0, 'pumpkin': 50.0 };
const GROWTH_TIMES = { 'carrot': 8.0, 'wheat': 20.0, 'pumpkin': 50.0 };
const PRESTIGE_MULTIPLIERS = { 'Python': 1.0, 'SQL': 10.0, 'JavaScript': 100.0 };
// --- SVG GRAPHICS GENERATORS ---
const SVGS = {
    balloon: `
    <svg class="hot-air-balloon" viewBox="0 0 64 80" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Balloon Envelope -->
        <path d="M12 28c0-11 9-20 20-20s20 9 20 20c0 6.2-2.8 11.7-7.2 15.4L38 52h-12l-6.8-8.6C14.8 39.7 12 34.2 12 28z" fill="#ef4444"/>
        <path d="M18 28c0-11 6.3-20 14-20s14 9 14 20c0 6.2-2 11.7-5 15.4L32 52l-9-8.6C20 39.7 18 34.2 18 28z" fill="#ffffff"/>
        <path d="M25 28c0-11 3.1-20 7-20s7 9 7 20c0 6.2-1 11.7-2.5 15.4L32 52l-4.5-8.6C26 39.7 25 34.2 25 28z" fill="#ef4444"/>
        <!-- Ropes -->
        <line x1="28" y1="52" x2="28" y2="58" stroke="#d97706" stroke-width="1.5"/>
        <line x1="36" y1="52" x2="36" y2="58" stroke="#d97706" stroke-width="1.5"/>
        <!-- Basket -->
        <rect x="25" y="58" width="14" height="10" rx="2" fill="#b45309"/>
        <!-- Cat Face inside -->
        <circle cx="32" cy="56" r="4" fill="#e4e4e7"/>
        <polygon points="29,54 29,50 31,53" fill="#e4e4e7"/>
        <polygon points="35,54 35,50 33,53" fill="#e4e4e7"/>
    </svg>`,
    cat: `
    <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Straw Hat -->
        <path d="M12 28h40v6H12z" fill="#d97706"/>
        <path d="M20 20h24v8H20z" fill="#f59e0b"/>
        <!-- Cat Head -->
        <rect x="18" y="32" width="28" height="20" rx="4" fill="#a8a29e"/>
        <polygon points="18,32 18,24 26,32" fill="#a8a29e"/>
        <polygon points="46,32 46,24 38,32" fill="#a8a29e"/>
        <!-- Eyes -->
        <rect x="23" y="38" width="4" height="4" fill="#1e293b"/>
        <rect x="37" y="38" width="4" height="4" fill="#1e293b"/>
        <!-- Snout -->
        <path d="M30 42h4l-2 2z" fill="#f43f5e"/>
        <!-- Hoe (Tool) -->
        <path d="M10 52l12-12m-2-2l4 4" stroke="#78350f" stroke-width="3"/>
        <rect x="8" y="50" width="6" height="4" fill="#64748b"/>
    </svg>`,
    
    frog: (level) => {
        let hatColor = '#10b981'; // Green cap (Python)
        let tool = `
            <!-- Water Sprinkler -->
            <path d="M12 45h6v12h-6z" fill="#94a3b8"/>
            <path d="M15 45v-4" stroke="#475569" stroke-width="2"/>
            <path d="M10 39c2-2 8-2 10 0" stroke="#38bdf8" stroke-dasharray="2 2" stroke-width="2"/>
        `;
        if (level === 2) {
            hatColor = '#3b82f6'; // Blue cap (SQL)
            tool = `
                <!-- Database Silo -->
                <rect x="10" y="42" width="10" height="15" rx="2" fill="#64748b" stroke="#475569" stroke-width="1"/>
                <line x1="10" y1="47" x2="20" y2="47" stroke="#334155"/>
                <line x1="10" y1="52" x2="20" y2="52" stroke="#334155"/>
            `;
        } else if (level === 3) {
            hatColor = '#06b6d4'; // Cyan cap (JS)
            tool = `
                <!-- Glowing Node/Device -->
                <circle cx="15" cy="48" r="5" fill="#0891b2"/>
                <circle cx="15" cy="48" r="7" stroke="#22d3ee" stroke-width="1" stroke-dasharray="2 2"/>
            `;
        }
        return `
        <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Frog Body -->
            <rect x="18" y="28" width="28" height="24" rx="10" fill="#4ade80"/>
            <!-- Eyes -->
            <circle cx="22" cy="24" r="7" fill="#4ade80"/>
            <circle cx="42" cy="24" r="7" fill="#4ade80"/>
            <circle cx="22" cy="24" r="3" fill="#111827"/>
            <circle cx="42" cy="24" r="3" fill="#111827"/>
            <!-- Mouth -->
            <path d="M26 40h12" stroke="#166534" stroke-width="2" stroke-linecap="round"/>
            <!-- Programmer Hat -->
            <path d="M16 22c5-3 27-3 32 0v4H16v-4z" fill="${hatColor}"/>
            <path d="M42 22l6 4v2" stroke="${hatColor}" stroke-width="2"/>
            ${tool}
        </svg>`;
    },
    crop: (type, progress) => {
        if (progress < 30) {
            // Sprout (Small green shoot)
            return `
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22V14M12 14c-1-1-3-1-4-3m4 3c1-1 3-1 4-3" stroke="#22c55e" stroke-width="2" stroke-linecap="round"/>
            </svg>`;
        }
        
        if (type === 'carrot') {
            if (progress < 90) {
                // Growing carrot
                return `
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 16v-6c-1-1-2-1-3-2M12 10c1-1 2-1 3-2" stroke="#15803d" stroke-width="2"/>
                    <path d="M10 20l2-4 2 4-2 2z" fill="#ea580c"/>
                </svg>`;
            } else {
                // Full grown carrot ready for harvest
                return `
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <!-- Leaves -->
                    <path d="M12 12V4M12 8c-2-2-4-1-5-3m5 3c2-2 4-1 5-3" stroke="#166534" stroke-width="2" stroke-linecap="round"/>
                    <!-- Large Orange Root -->
                    <path d="M8 12c0-2 8-2 8 0l-4 10z" fill="#f97316"/>
                    <path d="M10 15h4M9 18h6" stroke="#ea580c" stroke-width="1"/>
                </svg>`;
            }
        }
        
        if (type === 'wheat') {
            if (progress < 90) {
                // Young green wheat stalks
                return `
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 22V10M16 22V8" stroke="#16a34a" stroke-width="2"/>
                </svg>`;
            } else {
                // Golden ready wheat
                return `
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <!-- Golden swaying stalks -->
                    <path d="M8 22v-12c-1-1-2-2-1-4m1 4c1-1 2-2 1-4" stroke="#eab308" stroke-width="2" stroke-linecap="round"/>
                    <path d="M16 22v-14c-1-1-2-2-1-4m1 4c1-1 2-2 1-4" stroke="#eab308" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="7" cy="4" r="1.5" fill="#facc15"/>
                    <circle cx="9" cy="6" r="1.5" fill="#facc15"/>
                    <circle cx="15" cy="2" r="1.5" fill="#facc15"/>
                    <circle cx="17" cy="4" r="1.5" fill="#facc15"/>
                </svg>`;
            }
        }
        
        if (type === 'pumpkin') {
            if (progress < 90) {
                // Green pumpkin vines
                return `
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M4 20c4-4 12-4 16 0M8 12c2-2 6-2 8 0" stroke="#15803d" stroke-width="2" stroke-linecap="round"/>
                </svg>`;
            } else {
                // Giant ripe orange pumpkin
                return `
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <ellipse cx="12" cy="14" rx="8" ry="6" fill="#f97316"/>
                    <ellipse cx="12" cy="14" rx="5" ry="6" fill="#ea580c"/>
                    <path d="M12 8c0-2-1-4-2-5" stroke="#15803d" stroke-width="2" stroke-linecap="round"/>
                </svg>`;
            }
        }
        return '';
    }
};
// --- INITIALIZE & SYNC WITH BACKEND ---
function syncState() {
    fetch('/api/game/state')
        .then(res => res.json())
        .then(data => {
            if (data.status !== 'error') {
                updateLocalData(data);
                renderStats();
                renderFarm();
                
                // Alert if passive earnings accumulated offline
                if (data.passive_earned > 0) {
                    showJuiceNotification('Ingreso Pasivo', `¡Tus ranitas ganaron $${data.passive_earned} de oro mientras no estabas!`);
                    playSound('prestige');
                }
            }
        });
}
function updateLocalData(data) {
    userStats.username = data.username;
    userStats.gold = data.gold;
    userStats.prestige_count = data.prestige_count;
    userStats.active_language = data.active_language;
    userStats.porcentaje_auto = data.porcentaje_auto;
    userStats.auto_count = data.auto_count;
    plots = data.plots;
}
// Render Stats & Shop indicators
function renderStats() {
    // Balatro pulse when gold changes
    const goldEl = document.getElementById('txt-oro');
    const oldGold = parseFloat(goldEl.innerText.replace('$', '').replace(/,/g, ''));
    const newGold = userStats.gold;
    
    // Animate counter roll
    animateCounter('txt-oro', oldGold || 0, newGold, '$');
    
    if (newGold !== oldGold) {
        goldEl.classList.add('balatro-pulse', 'gold-glow');
        setTimeout(() => goldEl.classList.remove('balatro-pulse', 'gold-glow'), 250);
    }
    
    // General info
    document.getElementById('farm-name').innerText = `Mi Granja: ${userStats.username}`;
    document.getElementById('txt-auto').innerText = `${userStats.porcentaje_auto}% Automatizado (${userStats.auto_count}/64)`;
    document.getElementById('barra-auto').style.width = `${userStats.porcentaje_auto}%`;
    
    // Multiplier text
    const m = PRESTIGE_MULTIPLIERS[userStats.active_language] || 1.0;
    document.getElementById('prestige-mult').innerText = `x${m} Multiplicador`;
    
    // Shop Lock Overlays
    const sqlLocked = document.getElementById('sql-locked');
    const jsLocked = document.getElementById('js-locked');
    
    if (userStats.active_language === 'Python') {
        sqlLocked.classList.remove('hidden');
        jsLocked.classList.add('hidden');
    } else if (userStats.active_language === 'SQL') {
        sqlLocked.classList.add('hidden');
        jsLocked.classList.remove('hidden');
    } else {
        sqlLocked.classList.add('hidden');
        jsLocked.classList.add('hidden');
    }
}
// Generate the 64 plot grid DOM elements if empty, else update
function renderFarm() {
    const granja = document.getElementById('granja');
    
    // Initialize if first time
    if (granja.children.length === 0) {
        granja.innerHTML = '';
        for (let idx = 0; idx < 64; idx++) {
            const tile = document.createElement('div');
            tile.className = "tile";
            tile.id = `tile-${idx}`;
            tile.setAttribute('data-coord', `[${Math.floor(idx/8)},${idx%8}]`);
            
            // Matrix layer
            const matrix = document.createElement('div');
            matrix.className = "matrix-overlay hidden";
            matrix.id = `matrix-${idx}`;
            tile.appendChild(matrix);
            
            // Crop container
            const cropDiv = document.createElement('div');
            cropDiv.className = "crop-container";
            cropDiv.id = `crop-${idx}`;
            tile.appendChild(cropDiv);
            
            // Avatar
            const avatarDiv = document.createElement('div');
            avatarDiv.className = "avatar-container";
            avatarDiv.id = `avatar-${idx}`;
            tile.appendChild(avatarDiv);
            
            // Progress Bar
            const prog = document.createElement('div');
            prog.className = "absolute bottom-0 left-0 right-0 h-1 bg-stone-800 hidden";
            prog.innerHTML = `<div id="prog-bar-${idx}" class="h-full bg-emerald-400 transition-all duration-300"></div>`;
            tile.appendChild(prog);
            
            tile.onclick = (e) => handlePlotClick(idx, e);
            granja.appendChild(tile);
        }
    }
    
    // Update individual plots
    plots.forEach(p => {
        const tile = document.getElementById(`tile-${p.plot_index}`);
        const matrix = document.getElementById(`matrix-${p.plot_index}`);
        const crop = document.getElementById(`crop-${p.plot_index}`);
        const avatar = document.getElementById(`avatar-${p.plot_index}`);
        const prog = tile.querySelector('.absolute.bottom-0');
        const progBar = document.getElementById(`prog-bar-${p.plot_index}`);
        
        // Reset base classes
        tile.className = "tile";
        matrix.classList.add('hidden');
        prog.classList.add('hidden');
        
        if (p.cultivo !== 'vacio') {
            tile.classList.add('plowed');
            crop.innerHTML = SVGS.crop(p.cultivo, p.grow_progress);
            
            // Show progress bar if growing manually
            if (p.status === 'growing' && !p.automatizada) {
                prog.classList.remove('hidden');
                progBar.style.width = `${p.grow_progress}%`;
            }
        } else {
            crop.innerHTML = '';
        }
        
        // Automated states
        if (p.automatizada) {
            matrix.classList.remove('hidden');
            matrix.innerText = generateMatrixCode();
            
            if (p.nivel_auto === 1) tile.classList.add('auto-python');
            else if (p.nivel_auto === 2) tile.classList.add('auto-sql');
            else if (p.nivel_auto === 3) tile.classList.add('auto-js');
            
            avatar.innerHTML = SVGS.frog(p.nivel_auto);
        } else {
            // Manual gatico stands on empty/manual ready plots
            if (p.status === 'ready' || p.status === 'growing' || p.cultivo !== 'vacio') {
                avatar.innerHTML = SVGS.cat;
            } else {
                avatar.innerHTML = ''; // idle empty plot
            }
        }
    });
}
function generateMatrixCode() {
    const chars = "010101</>;=!";
    let res = "";
    for (let i = 0; i < 8; i++) {
        res += chars[Math.floor(Math.random() * chars.length)];
    }
    return res;
}
// --- INTERACTION HANDLERS ---
function handlePlotClick(idx, event) {
    const p = plots[idx];
    
    if (p.automatizada) {
        // Frog is working! No manual interaction.
        return;
    }
    
    if (p.status === 'empty' && p.cultivo === 'vacio') {
        // Sow crop
        const cost = SEED_COSTS[selectedCrop] * (PRESTIGE_MULTIPLIERS[userStats.active_language] || 1.0);
        if (userStats.gold >= cost) {
            playSound('plant');
            // Optimistic frontend update
            userStats.gold -= cost;
            p.cultivo = selectedCrop;
            p.status = 'growing';
            p.grow_progress = 0.0;
            renderStats();
            renderFarm();
            
            fetch('/api/game/click', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ plot_index: idx, action: 'plant', crop_type: selectedCrop })
            }).then(res => res.json()).then(data => {
                if (data.status === 'error') {
                    syncState(); // revert on error
                }
            });
        } else {
            playSound('fail');
            showJuiceNotification("Falta de Oro", `Necesitas $${cost} de oro para plantar ${selectedCrop}`);
        }
    } 
    else if (p.status === 'ready') {
        // Harvest crop
        playSound('harvest');
        
        fetch('/api/game/click', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ plot_index: idx, action: 'harvest' })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                const diff = data.gold_gained;
                createFloatingScore(event.clientX, event.clientY, `+$${diff}`);
                createSparks(event.clientX, event.clientY);
                syncState();
            }
        });
    }
    else if (p.status === 'growing') {
        // Click action generates manual click gold
        playSound('click');
        const mult = PRESTIGE_MULTIPLIERS[userStats.active_language] || 1.0;
        userStats.gold += 1.0 * mult;
        renderStats();
        
        createFloatingScore(event.clientX, event.clientY, `+$${1.0 * mult}`);
        createSparks(event.clientX, event.clientY);
        
        fetch('/api/game/click', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ plot_index: idx, action: 'click' })
        });
    }
}
// --- DUOLINGO STYLE CHALLENGE SYSTEM ---
function triggerAutomationChallenge(idx) {
    activeQuizPlot = idx;
    fetch(`/api/game/quiz/get`)
        .then(res => res.json())
        .then(data => {
            if (data.status === 'error') {
                showJuiceNotification('Error', data.message);
                return;
            }
            activeQuizId = data.quiz_id;
            activeQuizData = data;
            
            // Set up Modal
            document.getElementById('quiz-pregunta').innerText = data.question;
            
            const codeEl = document.getElementById('quiz-codigo');
            if (data.code_snippet) {
                codeEl.parentElement.classList.remove('hidden');
                codeEl.innerText = data.code_snippet;
            } else {
                codeEl.parentElement.classList.add('hidden');
            }
            
            // Build options buttons
            const container = document.getElementById('quiz-opciones');
            container.innerHTML = '';
            data.options.forEach((opt, index) => {
                const btn = document.createElement('button');
                btn.className = "w-full text-left p-4 rounded-2xl border-2 border-stone-700 bg-stone-800 text-stone-100 font-bold hover:bg-stone-700 hover:border-emerald-400 transition-all flex items-center justify-between group";
                btn.innerHTML = `
                    <span>${opt}</span>
                    <span class="opacity-0 group-hover:opacity-100 text-emerald-400 font-mono">[ Seleccionar ]</span>
                `;
                btn.onclick = () => submitQuizAnswer(index);
                container.appendChild(btn);
            });
            
            // Display modal
            document.getElementById('modal-duolingo').classList.remove('hidden');
        });
}
function submitQuizAnswer(selectedIndex) {
    fetch('/api/game/quiz/validate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            quiz_id: activeQuizId,
            selected_option_index: selectedIndex,
            plot_index: activeQuizPlot
        })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById('modal-duolingo').classList.add('hidden');
        
        if (data.correct) {
            playSound('levelUp');
            showJuiceNotification('¡Correcto!', data.message);
            
            // Animate frog placement bounce
            const tile = document.getElementById(`tile-${activeQuizPlot}`);
            tile.classList.add('animate__animated', 'animate__bounceIn');
            tile.addEventListener('animationend', () => tile.classList.remove('animate__animated', 'animate__bounceIn'));
            
            syncState();
        } else {
            playSound('fail');
            showJuiceNotification('Incorrecto', data.message);
        }
    });
}
function getQuizHint() {
    if (activeQuizData && activeQuizData.hint) {
        showJuiceNotification('Pista del Gatito 💡', activeQuizData.hint);
    }
}
// --- LANGUAGE LICENSE BUYING & PRESTIGE ---
function buyLanguageLicense(lang) {
    const cost = lang === 'SQL' ? 5000.0 : 10000.0;
    if (userStats.gold < cost) {
        playSound('fail');
        showJuiceNotification("Falta de Oro", `Necesitas $${cost} de oro para desbloquear el módulo de ${lang}`);
        return;
    }
    
    if (confirm(`¿Quieres vender tu granja al Banco Central y comprar la licencia de ${lang} por $${cost}? ¡Tu oro se reiniciará pero ganarás multiplicadores masivos!`)) {
        playSound('prestige');
        
        // Massive Prestige Animation Sequence
        const mainPanel = document.body;
        mainPanel.style.transition = 'filter 0.3s ease';
        mainPanel.style.filter = 'brightness(2) contrast(1.5) saturate(2)';
        
        fetch('/api/game/shop/buy_language', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ language: lang })
        })
        .then(res => res.json())
        .then(data => {
            setTimeout(() => {
                mainPanel.style.filter = 'none';
                if (data.status === 'success') {
                    showJuiceNotification('¡PRESTIGIO ALCANZADO!', data.message);
                    syncState();
                    syncLeaderboard();
                } else {
                    showJuiceNotification('Error', data.message);
                }
            }, 500);
        });
    }
}
// --- MULTIPLAYER RANKING ---
function syncLeaderboard() {
    fetch('/api/game/leaderboard')
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById('tabla-ranking');
            tbody.innerHTML = '';
            
            data.forEach((player, index) => {
                const tr = document.createElement('tr');
                // Highlight user row
                if (player.username.includes('(Tú)')) {
                    tr.className = "bg-stone-800 text-amber-400 font-bold border-l-4 border-amber-400";
                } else {
                    tr.className = "hover:bg-stone-800/40 text-stone-300";
                }
                
                tr.innerHTML = `
                    <td class="p-3 flex items-center gap-2">
                        <span class="text-xs text-stone-500 font-mono">#${index+1}</span>
                        <span>${player.username}</span>
                    </td>
                    <td class="p-3 text-center font-mono">${player.porcentaje_auto}%</td>
                    <td class="p-3 text-right font-semibold text-emerald-400 font-mono">$${player.gold.toLocaleString()}</td>
                `;
                tbody.appendChild(tr);
            });
        });
}
// --- JUICE ANIMATIONS AND POPUPS HELPERS ---
function animateCounter(id, start, end, prefix = '') {
    const obj = document.getElementById(id);
    if (!obj) return;
    
    const range = end - start;
    if (range === 0) {
        obj.innerText = `${prefix}${end.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        return;
    }
    
    let current = start;
    const duration = 500; // ms
    const stepTime = 30; // ms
    const increment = range / (duration / stepTime);
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            clearInterval(timer);
            obj.innerText = `${prefix}${end.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        } else {
            obj.innerText = `${prefix}${current.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        }
    }, stepTime);
}
function createFloatingScore(x, y, text) {
    const el = document.createElement('div');
    el.className = "floating-score";
    el.innerText = text;
    el.style.left = `${x - 20}px`;
    el.style.top = `${y - 30}px`;
    document.body.appendChild(el);
    
    el.addEventListener('animationend', () => el.remove());
}
function createSparks(x, y) {
    for (let i = 0; i < 8; i++) {
        const p = document.createElement('div');
        p.className = "particle";
        p.style.left = `${x}px`;
        p.style.top = `${y}px`;
        
        // Random explosion angle/velocity
        const angle = Math.random() * Math.PI * 2;
        const radius = Math.random() * 40 + 20;
        const tx = Math.cos(angle) * radius;
        const ty = Math.sin(angle) * radius;
        
        p.style.setProperty('--tx', `${tx}px`);
        p.style.setProperty('--ty', `${ty}px`);
        
        document.body.appendChild(p);
        p.addEventListener('animationend', () => p.remove());
    }
}
function showJuiceNotification(title, content) {
    const notif = document.getElementById('notificacion-gatito');
    document.getElementById('gatito-tema').innerText = title;
    document.getElementById('gatito-consejo').innerText = content;
    
    notif.classList.remove('hidden', 'animate__fadeOutDown');
    notif.classList.add('animate__fadeInUp');
}
function cerrarGatito() {
    const notif = document.getElementById('notificacion-gatito');
    notif.classList.add('animate__fadeOutDown');
    setTimeout(() => notif.classList.add('hidden'), 500);
}
// Select seed in shop
function selectSeed(type) {
    selectedCrop = type;
    document.querySelectorAll('.seed-btn').forEach(btn => {
        btn.classList.remove('border-amber-400', 'bg-amber-950/20');
        btn.classList.add('border-stone-700');
    });
    const activeBtn = document.getElementById(`btn-seed-${type}`);
    if (activeBtn) {
        activeBtn.classList.remove('border-stone-700');
        activeBtn.classList.add('border-amber-400', 'bg-amber-950/20');
    }
    playSound('click');
}
// Button click to trigger automate quiz selector
function selectPlotToAutomate() {
    playSound('click');
    showJuiceNotification("¿Cómo automatizar?", "Haz clic en el botón 'Desbloquear Script' y luego selecciona cualquier parcela en la granja para responder el Quiz!");
    
    // Switch cursor state or just highlight non-automated plots
    plots.forEach(p => {
        if (!p.automatizada) {
            const tile = document.getElementById(`tile-${p.plot_index}`);
            tile.style.outline = "2px dashed #f59e0b";
            
            // Override click handler temporarily to trigger quiz
            const originalClick = tile.onclick;
            tile.onclick = () => {
                // Restore click handlers
                plots.forEach(op => {
                    const ot = document.getElementById(`tile-${op.plot_index}`);
                    ot.style.outline = "none";
                    ot.onclick = (e) => handlePlotClick(op.plot_index, e);
                });
                triggerAutomationChallenge(p.plot_index);
            };
        }
    });
}
// --- CLIENT TICK LOOP (Every 1 second) ---
setInterval(() => {
    // 1. Locally increment crop progress for manual/auto plants
    plots.forEach(p => {
        if (p.cultivo !== 'vacio') {
            const growTime = GROWTH_TIMES[p.cultivo] || 8.0;
            
            if (p.automatizada) {
                // Automated ticks locally
                p.grow_progress += (1.0 / growTime) * 100.0;
                if (p.grow_progress >= 100.0) {
                    p.grow_progress = 0.0; // loops
                    
                    // Increment passive gold locally for instant juice response
                    const mult = PRESTIGE_MULTIPLIERS[userStats.active_language] || 1.0;
                    const cropVals = { 'carrot': 10.0, 'wheat': 30.0, 'pumpkin': 100.0 };
                    const yieldVal = (cropVals[p.cultivo] || 10.0) * mult;
                    
                    userStats.gold += yieldVal;
                    renderStats();
                    
                    // Floating score from frog center tile
                    const tile = document.getElementById(`tile-${p.plot_index}`);
                    if (tile) {
                        const rect = tile.getBoundingClientRect();
                        createFloatingScore(rect.left + 25, rect.top + 25, `+$${yieldVal}`);
                    }
                }
            } else {
                // Manual grows up to 100
                if (p.status === 'growing') {
                    p.grow_progress = Math.min(100.0, p.grow_progress + (1.0 / growTime) * 100.0);
                    if (p.grow_progress >= 100.0) {
                        p.status = 'ready';
                        playSound('click'); // notify player crop is ready
                    }
                }
            }
        }
    });
    
    renderFarm();
}, 1000);
// --- SERVER SYNC LOOP (Every 6 seconds) ---
setInterval(() => {
    syncState();
    syncLeaderboard();
}, 6000);
// --- GATITO TIPS CYCLE (Every 25 seconds) ---
setInterval(() => {
    fetch('/api/game/gatito')
        .then(res => res.json())
        .then(data => {
            showJuiceNotification(`Gatito Tips: ${data.tema} 🐱`, data.consejo);
        });
}, 25000);
// --- BOOTSTRAP ---
window.onload = () => {
    // Initial fetch
    syncState();
    syncLeaderboard();
    
    // Welcome message
    setTimeout(() => {
        showJuiceNotification("Bienvenido a Anurash! 🌾", "Siembra tus parcelas y acumula $100 de oro para comenzar a automatizar con tus primeros scripts de Python.");
    }, 1000);
};
