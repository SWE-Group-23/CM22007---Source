import { useState } from "react";

import Message from "./components/Message";

let messageId = 0;

function Chat() {
  const [messages, setMessages] = useState([
      { id: messageId++, mine: false, content: "Hi!" },
      { id: messageId++, mine: true, content: "Hi!" },
  ]);

  function addMessage(formData) {
      setMessages([
          ...messages,
          { id: messageId++, mine: true, content: formData.get("message") }
      ]);
  }

  return (
    <div className="chat-page">
      <div className="chat-top">
        <img className="chat-image" src="blank.png" alt="A dark grey silhouette on a light grey background." />
        <p className="chat-name">TomatoMagic23</p>
      </div>
      <div className="chat-middle">
        {messages.toReversed().map(message => {
          return <Message key={message.id} message={message} />
        })}
      </div>
      <div className="chat-bottom">
        <form className="chat-form" action={addMessage}>
          <input type="text" name="message" />
          <input className="dark-button" type="submit" value="Send" />
        </form>
      </div>
    </div>
  )
}

export default Chat;
