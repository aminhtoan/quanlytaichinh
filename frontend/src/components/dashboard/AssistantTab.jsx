function AssistantTab({
  aiParseText,
  setAiParseText,
  parseAiText,
  aiParseResult,
  wallets,
  setOcrFile,
  ocrWalletId,
  setOcrWalletId,
  scanOcr,
  ocrResult,
  chatMessage,
  setChatMessage,
  askChatbot,
  chatLoading,
  loadChatHistory,
  chatSessionId,
  chatReply,
  chatChartData,
  chatHistory,
}) {
  return (
    <section className="grid two-cols">
      <article className="card form">
        <h3 className="section-title">AI Parse (Smart Input)</h3>
        <textarea
          value={aiParseText}
          onChange={(event) => setAiParseText(event.target.value)}
          placeholder='Ví dụ: "Sáng nay ăn phở 50k"'
        />
        <button className="btn btn-primary" type="button" onClick={parseAiText}>
          Phân tích câu lệnh
        </button>
        {aiParseResult && <pre className="json-box">{JSON.stringify(aiParseResult, null, 2)}</pre>}
      </article>

      <article className="card form">
        <h3 className="section-title">OCR hóa đơn</h3>
        <label className="field-label">Ví nhận giao dịch từ OCR</label>
        <select value={ocrWalletId} onChange={(event) => setOcrWalletId(event.target.value)}>
          {wallets.map((wallet) => (
            <option key={wallet.id} value={wallet.id}>
              {wallet.name}
            </option>
          ))}
        </select>
        <input type="file" accept="image/*" onChange={(event) => setOcrFile(event.target.files?.[0] || null)} />
        <button className="btn btn-soft" type="button" onClick={scanOcr}>
          Quét OCR
        </button>
        {ocrResult && <pre className="json-box">{JSON.stringify(ocrResult, null, 2)}</pre>}
      </article>

      <article className="card full-width form">
        <h3 className="section-title">Chatbot tài chính</h3>
        <small className="chat-note">Sử dụng endpoint RAG: /chat/ask và tự động lưu session.</small>
        <textarea
          value={chatMessage}
          onChange={(event) => setChatMessage(event.target.value)}
          placeholder='Ví dụ: "Tháng này tôi nên tiết kiệm như thế nào?"'
        />
        <div className="row-actions">
          <button className="btn btn-primary" type="button" onClick={askChatbot} disabled={chatLoading}>
            {chatLoading ? "Đang trả lời..." : "Hỏi AI"}
          </button>
          <button
            className="btn btn-outline"
            type="button"
            onClick={() => loadChatHistory(chatSessionId)}
            disabled={!chatSessionId}
          >
            Tải lịch sử hội thoại
          </button>
        </div>

        {chatSessionId && <p className="helper-text">Session ID: {chatSessionId}</p>}
        {chatReply && <p className="chat-answer">{chatReply}</p>}
        {chatChartData && <pre className="json-box">{JSON.stringify(chatChartData, null, 2)}</pre>}

        <div className="chat-history">
          <h4 className="section-title subheading">Lịch sử hội thoại</h4>
          {chatHistory.length === 0 && <p className="empty-row">Chưa có lịch sử.</p>}
          {chatHistory.map((item, idx) => (
            <div key={`${item.sender}-${idx}`} className={`chat-bubble ${item.sender === "user" ? "user" : "bot"}`}>
              <strong>{item.sender === "user" ? "Bạn" : "Trợ lý"}:</strong> {item.text}
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}

export default AssistantTab;
