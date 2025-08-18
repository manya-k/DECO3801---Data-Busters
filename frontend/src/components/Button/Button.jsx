import "./Button.css";

function Button({title, baseButton, action}) {
    return (
        <button className={baseButton} onClick={action}>
            {title}
        </button>
    )
}

export default Button;