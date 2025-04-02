function Message({message}) {
    return <p className={message.mine ? "my-message" : "their-message"}>
        {message.content}
    </p>
}

export default Message;
