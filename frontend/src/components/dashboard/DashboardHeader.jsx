function DashboardHeader({ user, onLogout }) {
  return (
    <header className="card header top-banner">
      <div>
        <h1 className="page-title">Bảng điều khiển tài chính</h1>
        <p className="page-subtitle">
          Quản lý toàn diện thu chi, ngân sách, công nợ và đầu tư trong một nơi.
        </p>
        {user && <p className="header-meta">Đăng nhập: {user.full_name} ({user.email})</p>}
      </div>
      <button className="btn btn-outline" onClick={onLogout}>
        Đăng xuất
      </button>
    </header>
  );
}

export default DashboardHeader;
