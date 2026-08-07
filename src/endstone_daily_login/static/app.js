// Daily Login Admin - Web Application

let authToken = null;
let currentConfig = {};
let enchantmentData = {};
let currentEditingItem = null;

// ========== Auth ==========

async function login() {
    const password = document.getElementById('password-input').value;
    const errorEl = document.getElementById('login-error');

    try {
        const response = await fetch('/api/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: password })
        });
        const data = await response.json();

        if (data.success) {
            authToken = data.token;
            localStorage.setItem('authToken', authToken);
            showApp();
        } else {
            errorEl.textContent = 'Invalid password';
            errorEl.classList.remove('hidden');
        }
    } catch (err) {
        errorEl.textContent = 'Connection error';
        errorEl.classList.remove('hidden');
    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('authToken');
    document.getElementById('app').classList.add('hidden');
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('password-input').value = '';
}

async function showApp() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');
    await loadConfig();
    await loadEnchantments();
}

// ========== API Helpers ==========

async function apiGet(endpoint) {
    const response = await fetch(endpoint, {
        headers: { 'Authorization': `Bearer ${authToken}` }
    });
    return response.json();
}

async function apiPost(endpoint, body) {
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    });
    return response.json();
}

// ========== Toast ==========

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// ========== Tab Navigation ==========

document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        tab.classList.add('active');
        document.getElementById(`${tab.dataset.tab}-tab`).classList.add('active');

        // Load players when switching to players tab
        if (tab.dataset.tab === 'players') {
            loadPlayers();
        }
    });
});

// ========== Load Config ==========

async function loadConfig() {
    try {
        currentConfig = await apiGet('/api/config');
        renderMoneyConfig();
        renderItemsConfig();
        renderStructuresConfig();
        renderSettingsConfig();
    } catch (err) {
        showToast('Failed to load config', 'error');
    }
}

async function loadEnchantments() {
    try {
        const data = await apiGet('/api/enchantments');
        enchantmentData = data.enchantments || {};
    } catch (err) {
        console.error('Failed to load enchantments', err);
    }
}

// ========== Money Config ==========

function renderMoneyConfig() {
    const config = currentConfig.money || { amounts: [1000], randomize: false, enabled: true };

    document.getElementById('money-enabled').checked = config.enabled;
    document.getElementById('money-randomize').checked = config.randomize;

    const container = document.getElementById('money-amounts');
    container.innerHTML = '';

    (config.amounts || [1000]).forEach((amount, index) => {
        const row = document.createElement('div');
        row.className = 'amount-row';
        row.innerHTML = `
            <span>Day ${index + 1}</span>
            <input type="number" value="${amount}" data-index="${index}">
            <button class="btn-danger btn-small" onclick="removeMoneyAmount(${index})">✕</button>
        `;
        container.appendChild(row);
    });
}

function addMoneyAmount() {
    if (!currentConfig.money) currentConfig.money = { amounts: [], enabled: true, randomize: false };
    currentConfig.money.amounts.push(1000);
    renderMoneyConfig();
}

function removeMoneyAmount(index) {
    currentConfig.money.amounts.splice(index, 1);
    renderMoneyConfig();
}

async function saveMoney() {
    const amounts = [];
    document.querySelectorAll('#money-amounts input[type="number"]').forEach(input => {
        amounts.push(parseFloat(input.value) || 0);
    });

    const config = {
        amounts: amounts,
        enabled: document.getElementById('money-enabled').checked,
        randomize: document.getElementById('money-randomize').checked
    };

    try {
        await apiPost('/api/config/money', config);
        currentConfig.money = config;
        showToast('Money settings saved!');
    } catch (err) {
        showToast('Failed to save', 'error');
    }
}

// ========== Items Config ==========

function renderItemsConfig() {
    const config = currentConfig.items || { items: [], randomize: false, enabled: false };

    document.getElementById('items-enabled').checked = config.enabled;
    document.getElementById('items-randomize').checked = config.randomize;

    const container = document.getElementById('items-list');
    container.innerHTML = '';

    (config.items || []).forEach((item, index) => {
        const itemType = typeof item === 'object' ? item.type : item;
        const enchantments = typeof item === 'object' ? item.enchantments || {} : {};
        const enchantCount = Object.keys(enchantments).length;

        const row = document.createElement('div');
        row.className = 'item-row';

        const isEnchantable = enchantmentData[itemType] !== undefined;

        row.innerHTML = `
            <div class="item-info">
                <div class="item-name">${itemType.replace('minecraft:', '')}</div>
                <div class="item-enchants">${enchantCount > 0 ? `${enchantCount} enchantment(s)` : 'No enchantments'}</div>
            </div>
            ${isEnchantable ? `<button class="btn-secondary btn-small" onclick="openEnchantModal(${index})">⚡ Enchant</button>` : ''}
            <button class="btn-danger btn-small" onclick="removeItem(${index})">✕</button>
        `;
        container.appendChild(row);
    });
}

function addItem() {
    const input = document.getElementById('new-item-input');
    let itemId = input.value.trim();

    if (!itemId) return;
    if (!itemId.startsWith('minecraft:')) {
        itemId = 'minecraft:' + itemId;
    }

    if (!currentConfig.items) currentConfig.items = { items: [], enabled: false, randomize: false };

    // Check if enchantable
    if (enchantmentData[itemId]) {
        currentConfig.items.items.push({ type: itemId, enchantments: {} });
    } else {
        currentConfig.items.items.push({ type: itemId });
    }

    input.value = '';
    renderItemsConfig();
}

function removeItem(index) {
    currentConfig.items.items.splice(index, 1);
    renderItemsConfig();
}

async function saveItems() {
    const config = {
        items: currentConfig.items.items,
        enabled: document.getElementById('items-enabled').checked,
        randomize: document.getElementById('items-randomize').checked
    };

    try {
        await apiPost('/api/config/items', config);
        currentConfig.items = config;
        showToast('Item settings saved!');
    } catch (err) {
        showToast('Failed to save', 'error');
    }
}

// ========== Enchantment Modal ==========

function openEnchantModal(itemIndex) {
    currentEditingItem = itemIndex;
    const item = currentConfig.items.items[itemIndex];
    const itemType = typeof item === 'object' ? item.type : item;
    const enchantments = typeof item === 'object' ? item.enchantments || {} : {};

    document.getElementById('enchant-item-name').textContent = itemType;

    const container = document.getElementById('enchant-list');
    container.innerHTML = '';

    const compatible = enchantmentData[itemType] || [];

    compatible.forEach(ench => {
        const isEnabled = enchantments[ench.id] !== undefined;
        const level = enchantments[ench.id] || 1;

        const row = document.createElement('div');
        row.className = 'enchant-row';
        row.innerHTML = `
            <label>
                <input type="checkbox" data-enchant="${ench.id}" ${isEnabled ? 'checked' : ''}>
                ${ench.name}
            </label>
            <input type="range" min="1" max="10" value="${level}" data-enchant-level="${ench.id}" 
                   oninput="this.nextElementSibling.textContent = this.value">
            <span>${level}</span>
        `;
        container.appendChild(row);
    });

    document.getElementById('enchant-modal').classList.remove('hidden');
}

function closeEnchantModal() {
    document.getElementById('enchant-modal').classList.add('hidden');
    currentEditingItem = null;
}

function saveEnchantments() {
    const enchantments = {};

    document.querySelectorAll('#enchant-list input[type="checkbox"]:checked').forEach(checkbox => {
        const enchantId = checkbox.dataset.enchant;
        const levelInput = document.querySelector(`input[data-enchant-level="${enchantId}"]`);
        enchantments[enchantId] = parseInt(levelInput.value);
    });

    const item = currentConfig.items.items[currentEditingItem];
    if (typeof item === 'object') {
        item.enchantments = enchantments;
    } else {
        currentConfig.items.items[currentEditingItem] = {
            type: item,
            enchantments: enchantments
        };
    }

    closeEnchantModal();
    renderItemsConfig();
    showToast('Enchantments updated! Remember to save.');
}

// ========== Structures Config ==========

function renderStructuresConfig() {
    const config = currentConfig.structures || { structures: [], randomize: false, enabled: false };

    document.getElementById('structures-enabled').checked = config.enabled;
    document.getElementById('structures-randomize').checked = config.randomize;

    const container = document.getElementById('structures-list');
    container.innerHTML = '';

    (config.structures || []).forEach((structure, index) => {
        const row = document.createElement('div');
        row.className = 'structure-row';
        row.innerHTML = `
            <span>Day ${index + 1}</span>
            <input type="text" value="${structure}" data-index="${index}">
            <button class="btn-danger btn-small" onclick="removeStructure(${index})">✕</button>
        `;
        container.appendChild(row);
    });
}

function addStructure() {
    if (!currentConfig.structures) currentConfig.structures = { structures: [], enabled: false, randomize: false };
    currentConfig.structures.structures.push('mystructure');
    renderStructuresConfig();
}

function removeStructure(index) {
    currentConfig.structures.structures.splice(index, 1);
    renderStructuresConfig();
}

async function saveStructures() {
    const structures = [];
    document.querySelectorAll('#structures-list input[type="text"]').forEach(input => {
        if (input.value.trim()) structures.push(input.value.trim());
    });

    const config = {
        structures: structures,
        enabled: document.getElementById('structures-enabled').checked,
        randomize: document.getElementById('structures-randomize').checked
    };

    try {
        await apiPost('/api/config/structures', config);
        currentConfig.structures = config;
        showToast('Structure settings saved!');
    } catch (err) {
        showToast('Failed to save', 'error');
    }
}

// ========== Settings Config ==========

function renderSettingsConfig() {
    const forms = currentConfig.forms || {};
    const settings = currentConfig.settings || {};

    document.getElementById('admin-item').value = forms.adminItem || 'minecraft:compass';
    document.getElementById('claim-item').value = forms.claimItem || 'minecraft:stick';
    document.getElementById('entity-tag').value = forms.entityTag || 'daily_login';
    document.getElementById('interaction-type').value = forms.interactionType || 'Both';
    document.getElementById('currency-obj').value = settings.currencyObj || 'money';
}

async function saveFormConfig() {
    const config = {
        adminItem: document.getElementById('admin-item').value.trim() || 'minecraft:compass',
        claimItem: document.getElementById('claim-item').value.trim(),
        entityTag: document.getElementById('entity-tag').value.trim(),
        interactionType: document.getElementById('interaction-type').value
    };

    try {
        await apiPost('/api/config/forms', config);
        currentConfig.forms = config;
        showToast('Form config saved!');
    } catch (err) {
        showToast('Failed to save', 'error');
    }
}

async function saveSettings() {
    const config = {
        currencyObj: document.getElementById('currency-obj').value.trim() || 'money'
    };

    try {
        await apiPost('/api/config/settings', config);
        currentConfig.settings = config;
        showToast('Settings saved!');
    } catch (err) {
        showToast('Failed to save', 'error');
    }
}

// ========== Players ==========

async function loadPlayers() {
    try {
        const data = await apiGet('/api/players');
        const tbody = document.getElementById('players-body');
        tbody.innerHTML = '';

        (data.players || []).forEach(player => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${player.name}</td>
                <td>${player.streak}</td>
                <td>${player.longestStreak}</td>
                <td>
                    <button class="btn-secondary btn-small" onclick="resetClaim('${player.name}')">Reset Claim</button>
                    <button class="btn-secondary btn-small" onclick="resetStreak('${player.name}')">Reset Streak</button>
                </td>
            `;
            tbody.appendChild(row);
        });

        if (data.players.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4">No player data found</td></tr>';
        }
    } catch (err) {
        showToast('Failed to load players', 'error');
    }
}

async function resetClaim(playerName) {
    try {
        await apiPost(`/api/players/${encodeURIComponent(playerName)}/reset-claim`, {});
        showToast(`Reset claim for ${playerName}`);
        loadPlayers();
    } catch (err) {
        showToast('Failed to reset claim', 'error');
    }
}

async function resetStreak(playerName) {
    try {
        await apiPost(`/api/players/${encodeURIComponent(playerName)}/reset-streak`, {});
        showToast(`Reset streak for ${playerName}`);
        loadPlayers();
    } catch (err) {
        showToast('Failed to reset streak', 'error');
    }
}

// ========== Init ==========

document.addEventListener('DOMContentLoaded', () => {
    // Check for saved auth
    const savedToken = localStorage.getItem('authToken');
    if (savedToken) {
        authToken = savedToken;
        showApp();
    }

    // Enter key to login
    document.getElementById('password-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') login();
    });
});
