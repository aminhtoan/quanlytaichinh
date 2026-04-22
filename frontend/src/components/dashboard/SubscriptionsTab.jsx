function SubscriptionsTab({
  subscriptionForm,
  setSubscriptionForm,
  createSubscription,
  wallets,
  subscriptionSuggestions,
  subscriptions,
  toggleSubscription,
  removeSubscription,
  formatCurrency,
}) {
  return (
    <section className="grid two-cols">
      <form className="card form" onSubmit={createSubscription}>
        <h3 className="section-title">Tạo subscription</h3>
        <label className="field-label">Tên dịch vụ</label>
        <input
          value={subscriptionForm.name}
          onChange={(event) => setSubscriptionForm({ ...subscriptionForm, name: event.target.value })}
          required
        />
        <label className="field-label">Số tiền</label>
        <input
          type="number"
          min="1"
          value={subscriptionForm.amount}
          onChange={(event) => setSubscriptionForm({ ...subscriptionForm, amount: event.target.value })}
          required
        />
        <label className="field-label">Chu kỳ</label>
        <select
          value={subscriptionForm.frequency}
          onChange={(event) => setSubscriptionForm({ ...subscriptionForm, frequency: event.target.value })}
        >
          <option value="weekly">Tuần</option>
          <option value="monthly">Tháng</option>
          <option value="yearly">Năm</option>
        </select>
        <label className="field-label">Ví mặc định</label>
        <select
          value={subscriptionForm.default_wallet_id}
          onChange={(event) => setSubscriptionForm({ ...subscriptionForm, default_wallet_id: event.target.value })}
        >
          <option value="">Không chọn</option>
          {wallets.map((wallet) => (
            <option key={wallet.id} value={wallet.id}>{wallet.name}</option>
          ))}
        </select>
        <label className="field-label">Ngày đến hạn</label>
        <input
          type="datetime-local"
          value={subscriptionForm.next_due_date}
          onChange={(event) => setSubscriptionForm({ ...subscriptionForm, next_due_date: event.target.value })}
        />
        <button className="btn btn-primary" type="submit">Tạo subscription</button>
      </form>

      <article className="card">
        <h3 className="section-title">Gợi ý định kỳ từ AI</h3>
        <div className="chip-wrap">
          {subscriptionSuggestions.length === 0 && <span className="chip">Chưa có gợi ý</span>}
          {subscriptionSuggestions.map((item, idx) => (
            <span key={`${item.name}-${idx}`} className="chip chip-custom">
              {item.name}: {formatCurrency(item.amount)} ({Math.round(item.confidence * 100)}%)
            </span>
          ))}
        </div>
        <h4 className="section-title subheading">Danh sách subscription</h4>
        <table>
          <thead>
            <tr>
              <th>Tên</th>
              <th>Số tiền</th>
              <th>Trạng thái</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {subscriptions.length === 0 && (
              <tr><td colSpan="4" className="empty-row">Chưa có subscription.</td></tr>
            )}
            {subscriptions.map((item) => (
              <tr key={item.id}>
                <td>{item.name}</td>
                <td>{formatCurrency(item.amount)}</td>
                <td>{item.is_active ? "Đang chạy" : "Tạm dừng"}</td>
                <td>
                  <div className="row-actions">
                    <button className="btn btn-small btn-outline" onClick={() => toggleSubscription(item)}>
                      {item.is_active ? "Tạm dừng" : "Kích hoạt"}
                    </button>
                    <button className="btn btn-small btn-danger" onClick={() => removeSubscription(item.id)}>
                      Xóa
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </section>
  );
}

export default SubscriptionsTab;
