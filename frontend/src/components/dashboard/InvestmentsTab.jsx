function InvestmentsTab({
  investmentCreateForm,
  setInvestmentCreateForm,
  createInvestment,
  investmentUpdateForm,
  setInvestmentUpdateForm,
  updateInvestment,
  investmentSellForm,
  setInvestmentSellForm,
  sellInvestment,
  wallets,
  investmentOutcome,
}) {
  return (
    <section className="grid three-cols">
      <form className="card form" onSubmit={createInvestment}>
        <h3 className="section-title">Mở khoản đầu tư</h3>
        <label className="field-label">Ví</label>
        <select
          value={investmentCreateForm.wallet_id}
          onChange={(event) => setInvestmentCreateForm({ ...investmentCreateForm, wallet_id: event.target.value })}
          required
        >
          {wallets.map((wallet) => (
            <option key={wallet.id} value={wallet.id}>{wallet.name}</option>
          ))}
        </select>
        <label className="field-label">Tên khoản đầu tư</label>
        <input
          value={investmentCreateForm.name}
          onChange={(event) => setInvestmentCreateForm({ ...investmentCreateForm, name: event.target.value })}
          required
        />
        <label className="field-label">Loại</label>
        <select
          value={investmentCreateForm.type}
          onChange={(event) => setInvestmentCreateForm({ ...investmentCreateForm, type: event.target.value })}
        >
          <option value="gold">Vàng</option>
          <option value="stock">Cổ phiếu</option>
          <option value="fund">Quỹ</option>
          <option value="crypto">Crypto</option>
          <option value="other">Khác</option>
        </select>
        <label className="field-label">Vốn ban đầu</label>
        <input
          type="number"
          min="1"
          value={investmentCreateForm.principal_amount}
          onChange={(event) =>
            setInvestmentCreateForm({ ...investmentCreateForm, principal_amount: event.target.value })
          }
          required
        />
        <button className="btn btn-primary" type="submit">Tạo khoản đầu tư</button>
      </form>

      <form className="card form" onSubmit={updateInvestment}>
        <h3 className="section-title">Cập nhật giá thị trường</h3>
        <label className="field-label">Investment ID</label>
        <input
          value={investmentUpdateForm.investment_id}
          onChange={(event) =>
            setInvestmentUpdateForm({ ...investmentUpdateForm, investment_id: event.target.value })
          }
          required
        />
        <label className="field-label">Giá trị hiện tại</label>
        <input
          type="number"
          min="1"
          value={investmentUpdateForm.current_value}
          onChange={(event) =>
            setInvestmentUpdateForm({ ...investmentUpdateForm, current_value: event.target.value })
          }
          required
        />
        <button className="btn btn-soft" type="submit">Cập nhật giá</button>
      </form>

      <form className="card form" onSubmit={sellInvestment}>
        <h3 className="section-title">Chốt khoản đầu tư</h3>
        <label className="field-label">Investment ID</label>
        <input
          value={investmentSellForm.investment_id}
          onChange={(event) => setInvestmentSellForm({ ...investmentSellForm, investment_id: event.target.value })}
          required
        />
        <label className="field-label">Ví nhận tiền</label>
        <select
          value={investmentSellForm.wallet_id}
          onChange={(event) => setInvestmentSellForm({ ...investmentSellForm, wallet_id: event.target.value })}
          required
        >
          {wallets.map((wallet) => (
            <option key={wallet.id} value={wallet.id}>{wallet.name}</option>
          ))}
        </select>
        <label className="field-label">Giá bán</label>
        <input
          type="number"
          min="1"
          value={investmentSellForm.selling_price}
          onChange={(event) => setInvestmentSellForm({ ...investmentSellForm, selling_price: event.target.value })}
          required
        />
        <label className="field-label">Ngày bán (optional)</label>
        <input
          type="datetime-local"
          value={investmentSellForm.date}
          onChange={(event) => setInvestmentSellForm({ ...investmentSellForm, date: event.target.value })}
        />
        <button className="btn btn-primary" type="submit">Chốt lời/lỗ</button>
      </form>

      <article className="card full-width">
        <h3 className="section-title">Kết quả thao tác đầu tư</h3>
        <p className="helper-text">
          API hiện chưa có endpoint danh sách đầu tư. Sau khi tạo, hệ thống tự điền Investment ID vào 2 form còn lại.
        </p>
        {!investmentOutcome && <p className="empty-row">Chưa có thao tác đầu tư nào.</p>}
        {investmentOutcome && (
          <pre className="json-box">{JSON.stringify(investmentOutcome, null, 2)}</pre>
        )}
      </article>
    </section>
  );
}

export default InvestmentsTab;
