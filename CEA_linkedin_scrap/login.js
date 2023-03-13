const fs = require('fs');

//Add your credentials here
login('tictacd1@gmail.com', '(c)kKmRmJPYr+C2')

async function login(username, password) {
    const jSessionID = await getJSessionID()
    const li_at = await getLiAt(jSessionID, username, password);
    if (li_at && jSessionID) {
        console.log("Login succesful 🎉");
        //Save
        var jsonContent = JSON.stringify({ jSessionID, li_at });
        fs.writeFile("saved-cookie.json", jsonContent, 'utf8', function (err) {
            if (err) {
                console.log("An error occured while writing JSON Object to File.");
                return console.log(err);
            }
            console.log("saved-cookie.json has been saved.");
        });

        return {li_at,jSessionID}
    }
}

async function getJSessionID() {
    var requestOptions = {
        method: 'GET',
        redirect: 'follow'
    };
    let response = await fetch("https://www.linkedin.com", requestOptions)
    if (response.status == 200) {
        const cookies = response.headers.get("set-cookie")
        const regex = /(?<=JSESSIONID=)(.*?)(?=;)/;
        let JSESSIONID = cookies.match(regex)[0];
       // console.log(`JSESSIONID COLLECTED: ${JSESSIONID}`);
        return JSESSIONID;
    } else { console.log('Cannot get the JSESSIONID') }
}

async function getLiAt(JSessionID, username, password) {
    var myHeaders = new Headers();
    myHeaders.append("cookie", `SESSIONID=${JSessionID}`);
    myHeaders.append("csrf-token", JSessionID);
    myHeaders.append("x-li-user-agent", " LIAuthLibrary:0.0.3");
    myHeaders.append("Content-Type", "application/x-www-form-urlencoded");

    var urlencoded = new URLSearchParams();
    urlencoded.append("session_key", username);
    urlencoded.append("session_password", password);
    urlencoded.append("JSESSIONID", password);

    var requestOptions = {
        method: 'POST',
        headers: myHeaders,
        body: urlencoded,
        redirect: 'follow'
    };
    let response = await fetch("https://www.linkedin.com/uas/authenticate", requestOptions)

    if (response.status == 200) {
        const cookies = response.headers.get("set-cookie")
        const regex = /(?<=li_at=)(.*?)(?=;)/;
        let li_at = cookies.match(regex)[0];
        //console.log(`Connected: ${li_at}`)
        return li_at
    } else {
        console.log('Login failed. Please check if you need to resolve a captcha.')
    }
}