import backgroundImg from "../../assets/background.jpg";
import "../BasePage/BasePage.css"

function BasePage({children}) {
    return (
        <div className="screen" style={{ backgroundImage: `url(${backgroundImg})` }}>
            {children}    
        </div>
    )
}

export default BasePage;