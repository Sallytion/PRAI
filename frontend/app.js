// Application State
let state = {
    user: null,
    token: null,
    repositories: [],
    trackedRepositories: [],
    reviews: [],
    currentRepo: null,
    currentReview: null
};

// API Base URL
const API_BASE = 'http://localhost:8000';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAuthentication();
});

// Check if user is authenticated
function checkAuthentication() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token') || localStorage.getItem('auth_token');
    
    if (token) {
        state.token = token;
        localStorage.setItem('auth_token', token);
        // Remove token from URL
        window.history.replaceState({}, document.title, '/');
        fetchCurrentUser();
    } else {
        showScreen('loginScreen');
    }
}

// Login with GitHub
function loginWithGitHub() {
    window.location.href = `${API_BASE}/auth/github/login`;
}

// Logout
function logout() {
    localStorage.removeItem('auth_token');
    state = { user: null, token: null, repositories: [], trackedRepositories: [], reviews: [] };
    showScreen('loginScreen');
    showToast('Logged out successfully');
}

// Fetch current user
async function fetchCurrentUser() {
    showLoading(true);
    try {
        const response = await apiRequest('/auth/me');
        state.user = response;
        updateUserInfo();
        await loadDashboard();
        showScreen('dashboardScreen');
    } catch (error) {
        console.error('Failed to fetch user:', error);
        showToast('Failed to authenticate', 'error');
        logout();
    } finally {
        showLoading(false);
    }
}

// Update user info in header
function updateUserInfo() {
    const userInfo = document.getElementById('userInfo');
    if (state.user) {
        userInfo.innerHTML = `
            <div class="user-profile">
                <img src="${state.user.avatar_url}" alt="${state.user.username}" class="avatar">
                <span class="username">${state.user.username}</span>
                <button class="btn btn-secondary btn-small" onclick="logout()">Logout</button>
            </div>
        `;
    }
}

// Load dashboard data
async function loadDashboard() {
    showLoading(true);
    try {
        await Promise.all([
            fetchTrackedRepositories(),
            fetchAvailableRepositories(),
            fetchReviews()
        ]);
    } finally {
        showLoading(false);
    }
}

// Fetch tracked repositories
async function fetchTrackedRepositories() {
    try {
        const response = await apiRequest('/api/repositories/tracked');
        state.trackedRepositories = response.repositories;
        renderTrackedRepositories();
    } catch (error) {
        console.error('Failed to fetch tracked repositories:', error);
    }
}

// Fetch available repositories
async function fetchAvailableRepositories() {
    try {
        const response = await apiRequest('/api/repositories/');
        state.repositories = response.repositories;
        renderAvailableRepositories();
    } catch (error) {
        console.error('Failed to fetch repositories:', error);
    }
}

// Fetch reviews
async function fetchReviews() {
    try {
        const response = await apiRequest('/api/reviews/');
        state.reviews = response.reviews;
        renderReviews();
    } catch (error) {
        console.error('Failed to fetch reviews:', error);
    }
}

// Render tracked repositories
function renderTrackedRepositories() {
    const container = document.getElementById('trackedRepos');
    
    if (state.trackedRepositories.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No tracked repositories yet. Add some from the Available Repositories tab!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = state.trackedRepositories.map(repo => `
        <div class="repo-card">
            <div class="repo-header">
                <h3 class="repo-name">${repo.full_name}</h3>
                <span class="badge ${repo.webhook_configured ? 'badge-success' : 'badge-warning'}">
                    ${repo.webhook_configured ? '✓ Webhook' : '⚠ No Webhook'}
                </span>
            </div>
            <p class="repo-description">${repo.description || 'No description'}</p>
            <div class="repo-actions">
                <button class="btn btn-primary btn-small" onclick="viewRepository('${repo.id}')">
                    View PRs
                </button>
                ${!repo.webhook_configured ? `
                    <button class="btn btn-secondary btn-small" onclick="setupWebhook('${repo.id}')">
                        Setup Webhook
                    </button>
                ` : ''}
                <button class="btn btn-danger btn-small" onclick="untrackRepository('${repo.id}')">
                    Untrack
                </button>
            </div>
        </div>
    `).join('');
}

// Render available repositories
function renderAvailableRepositories() {
    const container = document.getElementById('availableRepos');
    const tracked = state.trackedRepositories.map(r => r.full_name);
    const available = state.repositories.filter(r => !tracked.includes(r.full_name));
    
    if (available.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>All your repositories are already tracked!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = available.map(repo => `
        <div class="repo-card">
            <div class="repo-header">
                <h3 class="repo-name">${repo.full_name}</h3>
                <span class="badge badge-info">${repo.private ? '🔒 Private' : '🌐 Public'}</span>
            </div>
            <p class="repo-description">${repo.description || 'No description'}</p>
            <div class="repo-actions">
                <button class="btn btn-primary btn-small" onclick="trackRepository('${repo.full_name}')">
                    Track Repository
                </button>
            </div>
        </div>
    `).join('');
}

// Render reviews
function renderReviews() {
    const container = document.getElementById('reviewsList');
    
    if (state.reviews.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No reviews yet. Reviews will appear here after PRs are analyzed.</p>
            </div>
        `;
        return;
    }
    
    const severityEmoji = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢',
        'info': '🔵'
    };
    
    container.innerHTML = state.reviews.map(review => `
        <div class="review-card" onclick="viewReview('${review.id}')">
            <div class="review-header">
                <div>
                    <h3 class="review-title">${review.repository_name} #${review.pr_number || '?'}</h3>
                    <p class="review-pr-title">${review.pr_title || 'Unknown PR'}</p>
                </div>
                <span class="badge badge-${review.status}">
                    ${review.status}
                </span>
            </div>
            <div class="review-meta">
                ${review.severity ? `
                    <span class="severity">
                        ${severityEmoji[review.severity] || '🔵'} ${review.severity.toUpperCase()}
                    </span>
                ` : ''}
                <span class="review-date">${new Date(review.created_at).toLocaleDateString()}</span>
            </div>
        </div>
    `).join('');
}

// Track repository
async function trackRepository(fullName) {
    showLoading(true);
    try {
        // Split fullName into owner/repo for the new endpoint
        const [owner, repo] = fullName.split('/');
        await apiRequest(`/api/repositories/track/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}`, 'POST');
        showToast('Repository tracked successfully!');
        await fetchTrackedRepositories();
        await fetchAvailableRepositories();
    } catch (error) {
        showToast('Failed to track repository', 'error');
    } finally {
        showLoading(false);
    }
}

// Untrack repository
async function untrackRepository(repoId) {
    if (!confirm('Are you sure you want to untrack this repository?')) return;
    
    showLoading(true);
    try {
        await apiRequest(`/api/repositories/${repoId}`, 'DELETE');
        showToast('Repository untracked');
        await fetchTrackedRepositories();
        await fetchAvailableRepositories();
    } catch (error) {
        showToast('Failed to untrack repository', 'error');
    } finally {
        showLoading(false);
    }
}

// Setup webhook
async function setupWebhook(repoId) {
    showLoading(true);
    try {
        await apiRequest(`/api/repositories/${repoId}/webhook`, 'POST');
        showToast('Webhook configured successfully!');
        await fetchTrackedRepositories();
    } catch (error) {
        showToast('Failed to setup webhook', 'error');
    } finally {
        showLoading(false);
    }
}

// View repository details
async function viewRepository(repoId) {
    console.log('viewRepository called with ID:', repoId);
    showLoading(true);
    try {
        const response = await apiRequest(`/api/repositories/${repoId}/pull-requests`);
        console.log('PR response:', response);
        state.currentRepo = state.trackedRepositories.find(r => r.id === repoId);
        console.log('Current repo:', state.currentRepo);
        renderRepositoryDetail(response.pull_requests);
        showScreen('repoDetailScreen');
    } catch (error) {
        console.error('Error loading PRs:', error);
        showToast('Failed to load PRs', 'error');
    } finally {
        showLoading(false);
    }
}

// Render repository detail
function renderRepositoryDetail(prs) {
    const container = document.getElementById('repoDetail');
    
    container.innerHTML = `
        <h1 class="page-title">${state.currentRepo.full_name}</h1>
        <p>${state.currentRepo.description || 'No description'}</p>
        
        <h2 class="section-title">Pull Requests</h2>
        ${prs.length === 0 ? `
            <div class="empty-state">
                <p>No open pull requests</p>
            </div>
        ` : `
            <div class="prs-list">
                ${prs.map(pr => `
                    <div class="pr-card">
                        <div class="pr-header">
                            <h3 class="pr-title">#${pr.number} ${pr.title}</h3>
                            <span class="badge badge-${pr.state}">${pr.state}</span>
                        </div>
                        <p class="pr-meta">
                            By ${pr.author} • 
                            +${pr.additions} −${pr.deletions} • 
                            ${pr.changed_files} files
                        </p>
                        <div class="pr-actions">
                            <a href="${pr.url}" target="_blank" class="btn btn-secondary btn-small">
                                View on GitHub
                            </a>
                            <button class="btn btn-primary btn-small" onclick="triggerReview('${state.currentRepo.id}', ${pr.number})">
                                🤖 Review Now
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `}
    `;
}

// Trigger manual review
async function triggerReview(repoId, prNumber) {
    showLoading(true);
    try {
        const response = await apiRequest(`/api/reviews/repository/${repoId}/pr/${prNumber}`, 'POST');
        showToast('✅ Review completed successfully!');
        
        // Refresh reviews immediately
        await fetchReviews();
        
        // If we have a review_id, optionally show it
        if (response.review_id) {
            console.log('Review ID:', response.review_id);
        }
    } catch (error) {
        showToast('❌ Review failed: ' + (error.message || 'Unknown error'), 'error');
        console.error('Review error:', error);
    } finally {
        showLoading(false);
    }
}

// View review details
async function viewReview(reviewId) {
    showLoading(true);
    try {
        const response = await apiRequest(`/api/reviews/${reviewId}`);
        state.currentReview = response;
        renderReviewDetail();
        showScreen('reviewDetailScreen');
    } catch (error) {
        showToast('Failed to load review', 'error');
    } finally {
        showLoading(false);
    }
}

// Render review detail
function renderReviewDetail() {
    const review = state.currentReview;
    const container = document.getElementById('reviewDetail');
    
    const severityEmoji = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢',
        'info': '🔵'
    };
    
    // Helper to safely render analysis content
    const renderAnalysis = (data) => {
        if (!data) return '';
        
        // If it's an object, extract the 'report' or 'output' field
        if (typeof data === 'object') {
            const text = data.report || data.output || data.raw || JSON.stringify(data, null, 2);
            return marked.parse(text);
        }
        
        // If it's a string, parse it as markdown
        if (typeof data === 'string') {
            return marked.parse(data);
        }
        
        return String(data);
    };
    
    container.innerHTML = `
        <h1 class="page-title">Review #${review.id.substring(0, 8)}</h1>
        
        <div class="review-summary">
            <div class="summary-item">
                <strong>PR:</strong> 
                <a href="${review.pr_url || '#'}" target="_blank">#${review.pr_number || '?'} ${review.pr_title || 'Unknown'}</a>
            </div>
            <div class="summary-item">
                <strong>Status:</strong> 
                <span class="badge badge-${review.status}">${review.status}</span>
            </div>
            <div class="summary-item">
                <strong>Severity:</strong> 
                ${review.severity ? `
                    ${severityEmoji[review.severity]} ${review.severity.toUpperCase()}
                ` : 'N/A'}
            </div>
            <div class="summary-item">
                <strong>Execution Time:</strong> ${review.execution_time || 0}s
            </div>
        </div>
        
        ${review.overall_summary ? `
            <div class="review-section">
                <h2>📋 Summary</h2>
                <div class="content-box markdown-content">
                    ${renderAnalysis(review.overall_summary)}
                </div>
            </div>
        ` : ''}
        
        ${review.logic_analysis ? `
            <div class="review-section">
                <h2>🧠 Logic & Correctness Analysis</h2>
                <div class="content-box markdown-content">
                    ${renderAnalysis(review.logic_analysis)}
                </div>
            </div>
        ` : ''}
        
        ${review.readability_analysis ? `
            <div class="review-section">
                <h2>📖 Code Quality & Readability</h2>
                <div class="content-box markdown-content">
                    ${renderAnalysis(review.readability_analysis)}
                </div>
            </div>
        ` : ''}
        
        ${review.performance_analysis ? `
            <div class="review-section">
                <h2>⚡ Performance Analysis</h2>
                <div class="content-box markdown-content">
                    ${renderAnalysis(review.performance_analysis)}
                </div>
            </div>
        ` : ''}
        
        ${review.security_analysis ? `
            <div class="review-section">
                <h2>🔒 Security Audit</h2>
                <div class="content-box markdown-content">
                    ${renderAnalysis(review.security_analysis)}
                </div>
            </div>
        ` : ''}
        
        ${review.recommendations && review.recommendations.length > 0 ? `
            <div class="review-section">
                <h2>💡 Recommendations</h2>
                <ul class="recommendations-list">
                    ${review.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
        
        ${review.error_message ? `
            <div class="review-section error-section">
                <h2>❌ Error</h2>
                <div class="content-box">
                    <p>${review.error_message}</p>
                </div>
            </div>
        ` : ''}
    `;
}

// Tab switching
function showTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(`${tabName}Tab`).classList.add('active');
}

// Filter repositories
function filterRepositories() {
    const search = document.getElementById('repoSearch').value.toLowerCase();
    const tracked = state.trackedRepositories.map(r => r.full_name);
    const available = state.repositories.filter(r => !tracked.includes(r.full_name));
    const filtered = available.filter(r => 
        r.full_name.toLowerCase().includes(search) ||
        (r.description && r.description.toLowerCase().includes(search))
    );
    
    const container = document.getElementById('availableRepos');
    container.innerHTML = filtered.map(repo => `
        <div class="repo-card">
            <div class="repo-header">
                <h3 class="repo-name">${repo.full_name}</h3>
                <span class="badge badge-info">${repo.private ? '🔒 Private' : '🌐 Public'}</span>
            </div>
            <p class="repo-description">${repo.description || 'No description'}</p>
            <div class="repo-actions">
                <button class="btn btn-primary btn-small" onclick="trackRepository('${repo.full_name}')">
                    Track Repository
                </button>
            </div>
        </div>
    `).join('');
}

// Back to dashboard
function backToDashboard() {
    showScreen('dashboardScreen');
    state.currentRepo = null;
    state.currentReview = null;
}

// Show screen
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.style.display = 'none';
    });
    document.getElementById(screenId).style.display = 'block';
}

// Show loading spinner
function showLoading(show) {
    document.getElementById('loadingSpinner').style.display = show ? 'flex' : 'none';
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast toast-${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// API Request Helper
async function apiRequest(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (state.token) {
        options.headers['Authorization'] = `Bearer ${state.token}`;
    }
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    
    if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
    }
    
    return response.json();
}

// Simple markdown parser (for display)
const marked = {
    parse: (text) => {
        if (!text) return '';
        
        return text
            // Code blocks
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            // Inline code
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // Headers
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            // Bold
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            // Italic
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            // Unordered lists
            .replace(/^\* (.+)$/gim, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            // Ordered lists
            .replace(/^\d+\. (.+)$/gim, '<li>$1</li>')
            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
            // Line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            // Wrap in paragraph
            .replace(/^(.+)$/, '<p>$1</p>');
    }
};
