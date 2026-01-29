function Toolbar({ user, onLogout }) {
    return (
        <header className="toolbar">
            <div className="toolbar-menu">
                <button className="toolbar-btn">Application</button>
                <button className="toolbar-btn">Manage</button>
                <button className="toolbar-btn">Tools</button>
                <button className="toolbar-btn">Help</button>
            </div>

            <div className="toolbar-spacer"></div>

            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                {user?.name || 'User'}
            </span>
            <button className="btn" onClick={onLogout}>
                Logout
            </button>
        </header>
    );
}

export default Toolbar;
