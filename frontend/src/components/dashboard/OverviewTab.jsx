function OverviewTab({
  summary,
  wallets,
  activeDebts,
  activeSubscriptions,
  insights,
  recentTransactions,
  formatCurrency,
  formatDate,
}) {
  return (
    <>
      <section className="grid summary-grid">
        <article className="card summary-card summary-income">
          <p className="summary-label">Tổng thu</p>
          <p className="summary-value">{formatCurrency(summary.total_income)}</p>
        </article>
        <article className="card summary-card summary-expense">
          <p className="summary-label">Tổng chi</p>
          <p className="summary-value">{formatCurrency(summary.total_expense)}</p>
        </article>
        <article className="card summary-card summary-balance">
          <p className="summary-label">Số dư hiện tại</p>
          <p className="summary-value">{formatCurrency(summary.balance)}</p>
        </article>
      </section>

      <section className="grid three-cols">
        <article className="card compact-card">
          <p className="summary-label">Số ví</p>
          <p className="summary-value smaller">{wallets.length}</p>
        </article>
        <article className="card compact-card">
          <p className="summary-label">Nợ đang mở</p>
          <p className="summary-value smaller">{activeDebts}</p>
        </article>
        <article className="card compact-card">
          <p className="summary-label">Subscription hoạt động</p>
          <p className="summary-value smaller">{activeSubscriptions}</p>
        </article>
      </section>

      <section className="grid two-cols">
        <article className="card">
          <h3 className="section-title">Gợi ý tiết kiệm</h3>
          <ul className="bullet-list">
            {(insights.recommendations || []).length === 0 && <li>Chưa có gợi ý.</li>}
            {(insights.recommendations || []).map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>
        <article className="card">
          <h3 className="section-title">Cảnh báo bất thường</h3>
          <ul className="bullet-list">
            {(insights.anomalies || []).length === 0 && <li>Chưa phát hiện bất thường.</li>}
            {(insights.anomalies || []).map((item) => (
              <li key={item.id || `${item.category}-${item.amount}-${item.created_at}`}>
                • {item.category}: {formatCurrency(item.amount)}
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="card">
        <h3 className="section-title">Giao dịch gần đây</h3>
        <table>
          <thead>
            <tr>
              <th>Ngày</th>
              <th>Loại</th>
              <th>Danh mục</th>
              <th>Số tiền</th>
              <th>Ví</th>
            </tr>
          </thead>
          <tbody>
            {recentTransactions.length === 0 && (
              <tr>
                <td colSpan="5" className="empty-row">
                  Chưa có giao dịch nào.
                </td>
              </tr>
            )}
            {recentTransactions.map((item) => (
              <tr key={item.id}>
                <td>{formatDate(item.transaction_date)}</td>
                <td>{item.type === "income" ? "Thu" : "Chi"}</td>
                <td>{item.category}</td>
                <td>{formatCurrency(item.amount)}</td>
                <td>{wallets.find((wallet) => wallet.id === item.wallet_id)?.name || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

export default OverviewTab;
