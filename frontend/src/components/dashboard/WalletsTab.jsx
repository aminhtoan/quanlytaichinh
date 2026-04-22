function WalletsTab({ walletForm, setWalletForm, createWallet, wallets, deleteWallet, formatCurrency }) {
  return (
    <section className="grid two-cols">
      <form className="card form" onSubmit={createWallet}>
        <h3 className="section-title">Tạo ví mới</h3>
        <label className="field-label">Tên ví</label>
        <input
          value={walletForm.name}
          onChange={(event) => setWalletForm({ ...walletForm, name: event.target.value })}
          required
        />
        <label className="field-label">Loại ví</label>
        <select
          value={walletForm.type}
          onChange={(event) => setWalletForm({ ...walletForm, type: event.target.value })}
        >
          <option value="cash">Tiền mặt</option>
          <option value="bank">Ngân hàng</option>
          <option value="ewallet">Ví điện tử</option>
          <option value="credit">Thẻ tín dụng</option>
          <option value="other">Khác</option>
        </select>
        <label className="field-label">Tiền tệ</label>
        <input
          value={walletForm.currency}
          onChange={(event) => setWalletForm({ ...walletForm, currency: event.target.value })}
        />
        <label className="field-label">Số dư ban đầu</label>
        <input
          type="number"
          min="0"
          value={walletForm.initial_balance}
          onChange={(event) => setWalletForm({ ...walletForm, initial_balance: event.target.value })}
        />
        <button className="btn btn-primary" type="submit">Tạo ví</button>
      </form>

      <article className="card">
        <h3 className="section-title">Danh sách ví</h3>
        <table>
          <thead>
            <tr>
              <th>Tên</th>
              <th>Loại</th>
              <th>Số dư</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {wallets.length === 0 && (
              <tr>
                <td colSpan="4" className="empty-row">Chưa có ví.</td>
              </tr>
            )}
            {wallets.map((wallet) => (
              <tr key={wallet.id}>
                <td>{wallet.name}</td>
                <td>{wallet.type}</td>
                <td>{formatCurrency(wallet.balance)}</td>
                <td>
                  <button className="btn btn-danger btn-small" onClick={() => deleteWallet(wallet.id)}>
                    Xóa
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </section>
  );
}

export default WalletsTab;
