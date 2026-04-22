function BudgetsTab({ budgetForm, setBudgetForm, createBudget, categories, budgetProgress, formatCurrency }) {
  return (
    <section className="grid two-cols">
      <form className="card form" onSubmit={createBudget}>
        <h3 className="section-title">Thiết lập ngân sách</h3>
        <label className="field-label">Danh mục</label>
        <select
          value={budgetForm.category_id}
          onChange={(event) => setBudgetForm({ ...budgetForm, category_id: event.target.value })}
          required
        >
          {categories
            .filter((item) => item.type === "expense")
            .map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
        </select>
        <label className="field-label">Hạn mức</label>
        <input
          type="number"
          min="1"
          value={budgetForm.amount_limit}
          onChange={(event) => setBudgetForm({ ...budgetForm, amount_limit: event.target.value })}
          required
        />
        <label className="field-label">Chu kỳ</label>
        <select
          value={budgetForm.period}
          onChange={(event) => setBudgetForm({ ...budgetForm, period: event.target.value })}
        >
          <option value="weekly">Tuần</option>
          <option value="monthly">Tháng</option>
          <option value="quarterly">Quý</option>
          <option value="yearly">Năm</option>
        </select>
        <label className="field-label">Từ ngày</label>
        <input
          type="date"
          value={budgetForm.start_date}
          onChange={(event) => setBudgetForm({ ...budgetForm, start_date: event.target.value })}
          required
        />
        <label className="field-label">Đến ngày</label>
        <input
          type="date"
          value={budgetForm.end_date}
          onChange={(event) => setBudgetForm({ ...budgetForm, end_date: event.target.value })}
          required
        />
        <button className="btn btn-primary" type="submit">Lưu ngân sách</button>
      </form>

      <article className="card">
        <h3 className="section-title">Tiến độ ngân sách tháng</h3>
        <table>
          <thead>
            <tr>
              <th>Danh mục</th>
              <th>Hạn mức</th>
              <th>Đã chi</th>
              <th>Còn lại</th>
              <th>Cảnh báo</th>
            </tr>
          </thead>
          <tbody>
            {budgetProgress.length === 0 && (
              <tr>
                <td colSpan="5" className="empty-row">Chưa có dữ liệu ngân sách.</td>
              </tr>
            )}
            {budgetProgress.map((item) => (
              <tr key={item.budget_id}>
                <td>{item.category_name}</td>
                <td>{formatCurrency(item.limit)}</td>
                <td>{formatCurrency(item.spent)}</td>
                <td>{formatCurrency(item.remaining)}</td>
                <td>{item.warning ? "⚠️" : "OK"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </section>
  );
}

export default BudgetsTab;
