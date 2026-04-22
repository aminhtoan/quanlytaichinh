function DebtsTab({
  debtForm,
  setDebtForm,
  createDebt,
  repayForm,
  setRepayForm,
  repayDebt,
  wallets,
  debts,
  formatCurrency,
}) {
  return (
    <section className="grid two-cols">
      <form className="card form" onSubmit={createDebt}>
        <h3 className="section-title">Tạo khoản công nợ</h3>
        <label className="field-label">Tên đối tác</label>
        <input
          value={debtForm.creditor_name}
          onChange={(event) => setDebtForm({ ...debtForm, creditor_name: event.target.value })}
          required
        />
        <label className="field-label">Loại</label>
        <select
          value={debtForm.type}
          onChange={(event) => setDebtForm({ ...debtForm, type: event.target.value })}
        >
          <option value="payable">Khoản phải trả</option>
          <option value="receivable">Khoản cho vay / phải thu</option>
        </select>
        <label className="field-label">Ví</label>
        <select
          value={debtForm.wallet_id}
          onChange={(event) => setDebtForm({ ...debtForm, wallet_id: event.target.value })}
          required
        >
          {wallets.map((wallet) => (
            <option key={wallet.id} value={wallet.id}>{wallet.name}</option>
          ))}
        </select>
        <label className="field-label">Tổng tiền</label>
        <input
          type="number"
          min="1"
          value={debtForm.total_amount}
          onChange={(event) => setDebtForm({ ...debtForm, total_amount: event.target.value })}
          required
        />
        <button className="btn btn-primary" type="submit">Tạo khoản nợ</button>
      </form>

      <form className="card form" onSubmit={repayDebt}>
        <h3 className="section-title">Thanh toán / Thu hồi nợ</h3>
        <label className="field-label">Khoản nợ</label>
        <select
          value={repayForm.debt_id}
          onChange={(event) => setRepayForm({ ...repayForm, debt_id: event.target.value })}
          required
        >
          {debts.map((item) => (
            <option key={item.id} value={item.id}>
              {item.creditor_name} ({formatCurrency(item.remaining_amount)} còn lại)
            </option>
          ))}
        </select>
        <label className="field-label">Ví thanh toán/nhận tiền</label>
        <select
          value={repayForm.wallet_id}
          onChange={(event) => setRepayForm({ ...repayForm, wallet_id: event.target.value })}
          required
        >
          {wallets.map((wallet) => (
            <option key={wallet.id} value={wallet.id}>{wallet.name}</option>
          ))}
        </select>
        <label className="field-label">Số tiền</label>
        <input
          type="number"
          min="1"
          value={repayForm.amount}
          onChange={(event) => setRepayForm({ ...repayForm, amount: event.target.value })}
          required
        />
        <label className="field-label">Ngày (optional)</label>
        <input
          type="datetime-local"
          value={repayForm.date}
          onChange={(event) => setRepayForm({ ...repayForm, date: event.target.value })}
        />
        <button className="btn btn-soft" type="submit">Xác nhận thanh toán</button>
      </form>

      <article className="card full-width">
        <h3 className="section-title">Danh sách công nợ</h3>
        <table>
          <thead>
            <tr>
              <th>Đối tác</th>
              <th>Loại</th>
              <th>Tổng tiền</th>
              <th>Còn lại</th>
              <th>Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {debts.length === 0 && (
              <tr><td colSpan="5" className="empty-row">Chưa có công nợ.</td></tr>
            )}
            {debts.map((item) => (
              <tr key={item.id}>
                <td>{item.creditor_name}</td>
                <td>{item.type === "payable" ? "Phải trả" : "Phải thu"}</td>
                <td>{formatCurrency(item.total_amount)}</td>
                <td>{formatCurrency(item.remaining_amount)}</td>
                <td>{item.status === "active" ? "Đang mở" : "Đã đóng"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </section>
  );
}

export default DebtsTab;
