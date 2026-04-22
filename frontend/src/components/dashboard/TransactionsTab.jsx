function TransactionsTab({
  transactionForm,
  setTransactionForm,
  createTransaction,
  transferForm,
  setTransferForm,
  submitTransfer,
  queryForm,
  setQueryForm,
  runTransactionQuery,
  wallets,
  categories,
  queryResult,
  formatDate,
  formatCurrency,
  removeTransaction,
}) {
  return (
    <>
      <section className="grid three-cols">
        <form className="card form" onSubmit={createTransaction}>
          <h3 className="section-title">Thêm giao dịch</h3>
          <label className="field-label">Loại</label>
          <select
            value={transactionForm.type}
            onChange={(event) => setTransactionForm({ ...transactionForm, type: event.target.value })}
          >
            <option value="expense">Chi tiêu</option>
            <option value="income">Thu nhập</option>
          </select>

          <label className="field-label">Ví</label>
          <select
            value={transactionForm.wallet_id}
            onChange={(event) => setTransactionForm({ ...transactionForm, wallet_id: event.target.value })}
            required
          >
            {wallets.map((wallet) => (
              <option key={wallet.id} value={wallet.id}>
                {wallet.name}
              </option>
            ))}
          </select>

          <label className="field-label">Danh mục</label>
          <select
            value={transactionForm.category_id}
            onChange={(event) => {
              const selected = categories.find((item) => item.id === event.target.value);
              setTransactionForm({
                ...transactionForm,
                category_id: event.target.value,
                category: selected?.name || "",
              });
            }}
          >
            <option value="">Chọn danh mục</option>
            {categories.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>

          <label className="field-label">Số tiền</label>
          <input
            type="number"
            min="1"
            value={transactionForm.amount}
            onChange={(event) => setTransactionForm({ ...transactionForm, amount: event.target.value })}
            required
          />

          <label className="field-label">Ghi chú</label>
          <input
            value={transactionForm.note}
            onChange={(event) => setTransactionForm({ ...transactionForm, note: event.target.value })}
          />

          <label className="field-label">Thời gian</label>
          <input
            type="datetime-local"
            value={transactionForm.transaction_date}
            onChange={(event) =>
              setTransactionForm({ ...transactionForm, transaction_date: event.target.value })
            }
            required
          />
          <button className="btn btn-primary" type="submit">
            Lưu giao dịch
          </button>
        </form>

        <form className="card form" onSubmit={submitTransfer}>
          <h3 className="section-title">Chuyển tiền giữa ví</h3>
          <label className="field-label">Ví nguồn</label>
          <select
            value={transferForm.source_wallet_id}
            onChange={(event) => setTransferForm({ ...transferForm, source_wallet_id: event.target.value })}
            required
          >
            {wallets.map((wallet) => (
              <option key={wallet.id} value={wallet.id}>
                {wallet.name}
              </option>
            ))}
          </select>
          <label className="field-label">Ví đích</label>
          <select
            value={transferForm.dest_wallet_id}
            onChange={(event) => setTransferForm({ ...transferForm, dest_wallet_id: event.target.value })}
            required
          >
            {wallets.map((wallet) => (
              <option key={wallet.id} value={wallet.id}>
                {wallet.name}
              </option>
            ))}
          </select>
          <label className="field-label">Số tiền</label>
          <input
            type="number"
            min="1"
            value={transferForm.amount}
            onChange={(event) => setTransferForm({ ...transferForm, amount: event.target.value })}
            required
          />
          <label className="field-label">Ghi chú</label>
          <input
            value={transferForm.note}
            onChange={(event) => setTransferForm({ ...transferForm, note: event.target.value })}
          />
          <label className="field-label">Ngày</label>
          <input
            type="datetime-local"
            value={transferForm.date}
            onChange={(event) => setTransferForm({ ...transferForm, date: event.target.value })}
            required
          />
          <button className="btn btn-soft" type="submit">
            Chuyển tiền
          </button>
        </form>

        <article className="card form">
          <h3 className="section-title">Lọc giao dịch</h3>
          <label className="field-label">Từ ngày</label>
          <input
            type="date"
            value={queryForm.start_date}
            onChange={(event) => setQueryForm({ ...queryForm, start_date: event.target.value })}
          />
          <label className="field-label">Đến ngày</label>
          <input
            type="date"
            value={queryForm.end_date}
            onChange={(event) => setQueryForm({ ...queryForm, end_date: event.target.value })}
          />
          <label className="field-label">Ví</label>
          <select
            value={queryForm.wallet_id}
            onChange={(event) => setQueryForm({ ...queryForm, wallet_id: event.target.value })}
          >
            <option value="">Tất cả ví</option>
            {wallets.map((wallet) => (
              <option key={wallet.id} value={wallet.id}>
                {wallet.name}
              </option>
            ))}
          </select>
          <label className="field-label">Loại</label>
          <select
            value={queryForm.type}
            onChange={(event) => setQueryForm({ ...queryForm, type: event.target.value })}
          >
            <option value="">Tất cả</option>
            <option value="income">Thu</option>
            <option value="expense">Chi</option>
          </select>
          <button className="btn btn-outline" type="button" onClick={runTransactionQuery}>
            Áp dụng bộ lọc
          </button>
        </article>
      </section>

      <section className="card">
        <h3 className="section-title">Kết quả giao dịch</h3>
        <table>
          <thead>
            <tr>
              <th>Ngày</th>
              <th>Loại</th>
              <th>Danh mục</th>
              <th>Số tiền</th>
              <th>Ghi chú</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {(queryResult.items || []).length === 0 && (
              <tr>
                <td colSpan="6" className="empty-row">Không có dữ liệu.</td>
              </tr>
            )}
            {(queryResult.items || []).map((item) => (
              <tr key={item.id}>
                <td>{formatDate(item.transaction_date)}</td>
                <td>{item.type === "income" ? "Thu" : "Chi"}</td>
                <td>{item.category}</td>
                <td>{formatCurrency(item.amount)}</td>
                <td>{item.note}</td>
                <td>
                  <button className="btn btn-danger btn-small" onClick={() => removeTransaction(item.id)}>
                    Xóa
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="table-meta">Tổng bản ghi: {queryResult.total || 0}</p>
      </section>
    </>
  );
}

export default TransactionsTab;
