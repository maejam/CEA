const swaggerUi = require("swagger-ui-express");
const swaggerJsdoc = require("swagger-jsdoc");
const process = require("process");

const swaggerOptions = {
  definition: {
    openapi: "3.0.0",
    info: {
      title: "API",
      version: "1.0.0",
      description: "API description",
    },
  },
  apis: ["./index.js"], 
};

const swaggerSpecs = swaggerJsdoc(swaggerOptions);

const axios = require("axios");
const express = require("express");
const app = express();
//Si sous windows = mode dev, port = 8007
//Si sous linux (docker) = mode prod, port = 8002
const port = process.platform === "win32" ? 8007 : 8002;

const login = require("./login");

app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpecs));

const fs = require("fs");
var savedCookies = require("./saved-cookie.json");

/**
 * @swagger
 * /scrap:
 *   get:
 *     summary: Récupère les données
 *     parameters:
 *       - in: query
 *         name: keywords
 *         schema:
 *           type: array
 *           items:
 *             type: string
 *         required: true
 *         example: ["eco-design electronics", "ecoinnovation electronics technology semi-conductor", "climate change semi-conductor",    "climate change electronics technology ", "change innovation electronics technology", "sustainability electronics technology"]
 *     responses:
 *       200:
 *         description: Les données ont été récupérées avec succès
 *       404:
 *         description: Échec de la récupération des données
 */

const do_debug = false;

app.get("/scrap", async (req, res) => {
  try {
    const keywords = req.query.keywords;
    if (!keywords || !Array.isArray(keywords)) {
      res.status(400).send("Paramètre 'keywords' invalide ou manquant");
      return;
    }

    let response;
    if (!do_debug) {
      // Effectuer un appel à scrap
      response = await scrap(keywords);
      // Sauvegarder le contenu de response dans response.txt
      //fs.writeFileSync("response.txt", JSON.stringify(response));
    } else {
      // Charger le contenu de response.txt
      const data = fs.readFileSync("response.txt", "utf-8");
      response = JSON.parse(data);
    }
    if (response) {
      //bulkSave(response);
      response2 = await bulkSave(response);
      // log response2 to console
      console.log("Log response from crud api to console");
      console.log(response2);      
      res.send(response2);
    } else {
      //refresh cookie
      await login("tictacd1@gmail.com", "(c)kKmRmJPYr+C2");
      const response2 = await scrap(keywords);
      if (response2) {
        //bulkSave(response2);
        response2 = await bulkSave(response);
        console.log("Log response from crud api to console");
        console.log(response2);      
        res.send(response2);
      } else {
        res.status(404).send("Scrapping failed");
      }
    }
  } catch (error) {
    console.error("Error occurred:", error);
    res.status(500).send("Une erreur est survenue lors du scrapping");
  }
});



/**
 * @swagger
 * /:
 *   get:
 *     summary: Récupère la page d'accueil
 *     responses:
 *       200:
 *         description: La page d'accueil a été récupérée avec succès
 */
app.get("/", async (req, res) => {
  res.send("CEA LinkedIn listening at http://lk_scrap:8002");
});

app.listen(port, () => {
  console.log(`CEA LinkedIn listening at http://lk_scrap:${port}`);
});

async function bulkSave(response) {
  let finalPosts = response.influencersPosts.concat(response.keywordPosts);

  // Afficher le contenu JSON dans la console
  const jsonContent = JSON.stringify(finalPosts);
  //console.log("Contenu JSON :", jsonContent);

  // Sauvegarder jsonContent dans "jsoncontent.txt"
  /*fs.writeFile('jsoncontent.txt', jsonContent, (err) => {
    if (err) {
      console.log('Erreur lors de la sauvegarde du fichier:', err);
    } else {
      console.log('Contenu JSON sauvegardé dans "jsoncontent.txt"');
    }
  });*/
  //fs.writeFileSync("json_content2.txt", jsonContent);
  // Send JSON content to crud_api
  //crud_api_url = "http://crud_api:8000/document/document/bulk_linkedin/";
  //Si sous windows = mode dev, port = 8009
  //Si sous linux (docker) = mode prod, port = 8000
  // const port_crud_api_port = process.platform === "win32" ? 8009 : 8000;
  crud_api_url = process.platform === "win32"  ? "http://crud_api:8009/document/document/bulk_linkedin/" : "http://crud_api:8000/document/document/bulk_linkedin/";

  let config = {
    method: "post",
    maxBodyLength: Infinity,
    url: crud_api_url,
    headers: {
      "Content-Type": "application/json",
      "accept": "application/json"
    },
    data: jsonContent,
  };
  return axios.request(config)
    .then((response) => {
      //console.log(JSON.stringify(response.data));
      console.log("JSON content sent to crud_api");
      console.log(response.data);
      return response.data; 
    })
    .catch((error) => {
      console.log(error);
      //console.log("Error while sending JSON content to crud_api");
      return "Error while sending JSON content to crud_api - " + response.status;        
    });
}

async function scrap(keywords) {
  if (!Array.isArray(keywords) || keywords.length === 0) {
    throw new Error("Les mots-clés doivent être une liste non vide");
  }

  try {
    //with saved cookie
    let influencersPosts = await getInfluencersPost(
      savedCookies.jSessionID,
      savedCookies.li_at,
      "0"
    );
    // Count and log to console number of influencers posts
    console.log("Number of influencers posts: " + influencersPosts.length);

    let keywordPosts = await getKeywordPost(
      keywords[0],
      savedCookies.jSessionID,
      savedCookies.li_at,
      "0"
    );
    // Count and log to console number of keyword posts
    console.log("Number of keyword posts: " + keywordPosts.length);
    // log to console keywordPosts
    console.log("Log keywordPosts to console");
    console.log(keywordPosts);

    return { influencersPosts, keywordPosts };
  } catch (error) {
    console.log(error);
  }
}

async function getInfluencersPost(JSessionID, li_at, page) {
  var myHeaders = new Headers();
  myHeaders.append(
    "sec-ch-ua",
    '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"'
  );
  myHeaders.append("x-li-lang", "en_US");
  myHeaders.append("sec-ch-ua-mobile", "?0");
  myHeaders.append(
    "User-Agent",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
  );
  myHeaders.append(
    "x-li-page-instance",
    "urn:li:page:d_flagship3_search_srp_content;9Jk/0mB9QayeSLyzbrTm7w=="
  );
  myHeaders.append("accept", "application/vnd.linkedin.normalized+json+2.1");
  myHeaders.append("csrf-token", JSessionID);
  myHeaders.append(
    "x-li-track",
    '{"clientVersion":"1.11.7073","mpVersion":"1.11.7073","osName":"web","timezoneOffset":1,"timezone":"Europe/Paris","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":2,"displayWidth":3360,"displayHeight":2100}'
  );
  myHeaders.append("x-restli-protocol-version", "2.0.0");
  myHeaders.append("sec-ch-ua-platform", '"macOS"');
  myHeaders.append("host", "www.linkedin.com");
  myHeaders.append(
    "cookie",
    `bcookie=\"v=2&485bf273-f1ea-408c-8436-0c7181d9156a\"; bscookie=\"v=1&20220331200952da5c1cf9-c60a-4f45-8fbe-997d305e6e6fAQEieB4BOi-aELplBFCgAKociJcd7tVo\"; li_alerts=e30=; G_ENABLED_IDPS=google; li_rm=AQE-_Q47sMVN1AAAAX_7SisP4fSnUvub_AMBS8DX3xN2Eu20FeASz36VFYhegsKW2tKxYRCBFXqZ2Rww1tinbptPLWlK6xYr23NbWEUmCH8EZKCWHO-K6CCa; _gcl_au=1.1.627853441.1649188418; JSESSIONID=\"${JSessionID}\"; li_theme=light; li_theme_set=app; liveagent_oref=https://www.linkedin.com/sales/search/people?companyIncluded=Viz.ai:17897131&companyTimeScope=CURRENT&keywords=; liveagent_ptid=0c11ec91-722f-4d91-ab8e-dcc53f092c3a; li_ep_auth_context=AE9hcHA9YWNjb3VudENlbnRlcixhaWQ9MTMxNzIxMjM0LGlpZD0tMSxwaWQ9MTYwNTY2NjUwLGV4cD0xNjUzNzkxNDA3MzM0LGN1cj10cnVlAceGcKxcGNw9ucMq8pSVQqZbImUJ; mp_52e5e0805583e8a410f1ed50d8e0c049_mixpanel={\"distinct_id\": \"181e3a93a177ba-008caacecca3cb-1c525635-1aeaa0-181e3a93a18a01\",\"$device_id\": \"181e3a93a177ba-008caacecca3cb-1c525635-1aeaa0-181e3a93a18a01\",\"$initial_referrer\": \"$direct\",\"$initial_referring_domain\": \"$direct\"}; timezone=Europe/Paris; aam_uuid=80685154479845086341700446948648622153; g_state={\"i_l\":0}; li_gc=MTsyMTsxNjY4MjU5ODcyOzI7MDIxWajV8j0mtSOrq2fBZ8KsqrnDmOm+vtdW+wXqaJFpC7w=; liveagent_vc=46; lms_ads=AQE9bVheN-SIeAAAAYWMNhZBFgJJ-hn0SX63IfB1FZ7J6wauuOlxHEOeE5iCW5-yOPbP4CEJpnGhbnsd1JyvqiRJgr-hWQky; lms_analytics=AQFIUxW1CodFbAAAAYWMNhZBya07N2o26lxNtcOmjru3xHE3k6pIrgdT62J_zw9iinDcxwrlOd7yCx7HgmEpF02ojOIuCosC; UserMatchHistory=AQIaXwaX-TkKsgAAAYW-_0ENo_TJc7H8E0ZqJ2uf9JzurABuk1YnyBHjZ9WTeQb5Sg9dbny0QeLsmw; AnalyticsSyncHistory=AQJKxTz251rDqgAAAYW-_0ENLC2ZT3buDdb67UW9KuZJ1XwWpN6bOuk-JWC1ewe_-VxXwKRGoz0LDh8FLhFf6w; li_at=${li_at}; liap=true; lang=v=2&lang=en-us; AMCVS_14215E3D5995C57C0A495C55@AdobeOrg=1; lidc=\"b=TB78:s=T:r=T:a=T:p=T:g=2988:u=736:x=1:i=1674322747:t=1674409147:v=2:sig=AQFnL4oTbeOUk4qzra4l0whKoYkmOXei\"; AMCV_14215E3D5995C57C0A495C55@AdobeOrg=-637568504|MCIDTS|19380|MCMID|80136092929184719531681562577197067138|MCAAMLH-1674995348|6|MCAAMB-1674995348|6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y|MCOPTOUT-1674397748s|NONE|vVersion|5.1.1|MCCIDH|1587226822; li_mc=MTsyMTsxNjc0MzkwOTM5OzI7MDIxIrh1LncJm9MKnXd3HqrPsAwTm3FK6e1G2PBp+9I6HOI=; _dd_s=logs=1&id=56e3a073-6c12-4089-90e6-3312d4853a2a&created=1674390541135&expire=1674392080122`
  );

  var requestOptions = {
    method: "GET",
    headers: myHeaders,
    redirect: "follow",
  };
  let response = await fetch(
    `https://www.linkedin.com/voyager/api/search/dash/clusters?decorationId=com.linkedin.voyager.dash.deco.search.SearchClusterCollection-175&origin=FACETED_SEARCH&q=all&query=(flagshipSearchIntent:SEARCH_SRP,queryParameters:(datePosted:List(past-week),fromMember:List(ACoAAA8dVUgBv-9Y9uEz5K8y2bFmm56ivV7fG8E,ACoAABsfY9MBZPzdGejocT7IiWRpOgeWCQtTa00,ACoAACqkq6YBXD-AMlAmLUcp28BxEWD9QNme0Z0,ACoAAAYJ-P4B8XcfHOiVTdmiAyYGfvxBRs3J_Ug),resultType:List(CONTENT)),includeFiltersInResponse:false)&start=${page}`,
    requestOptions
  );
  console.log(response.status);
  if (response.status == 200) {
    let json = await response.json();
    const elements = json["included"];
    let reactions = [];
    let posts = [];
    for (const e of elements) {
      if (e["numLikes"]) {
        reactions.push({
          postID: e["entityUrn"].split(
            "urn:li:fsd_socialActivityCounts:urn:li:activity:"
          )[1],
          likes: e["numLikes"],
          comments: e["numComments"],
        });
      } else {
        if (e["template"]) {
          posts.push({
            postID: e["trackingUrn"].split("urn:li:activity:")[1],
            author: e["title"]["text"],
            authorID: e["actorTrackingUrn"].split("urn:li:member:")[1],
            content: e["summary"]["text"],
            date_string: e["secondarySubtitle"]["text"],
          });
        }
      }
    }
    const results = posts.map((t1) => ({
      ...t1,
      ...reactions.find((t2) => t2.postID === t1.postID),
    }));
    //Save results
    /*         var jsonContent = JSON.stringify({ "posts": results });
                fs.writeFile(`influenceurs-posts-p${page}.json`, jsonContent, 'utf8', function (err) {
                    if (err) {
                        console.log("An error occured while writing JSON Object to File.");
                        return console.log(err);
                    }
                    console.log("Influenceurs posts has been saved.");
                }); */
    return results;
  } else {
    console.log("Error GET Influenceurs Posts");
  }
}

async function getKeywordPost(keyword, JSessionID, li_at, page) {
  const encodedKeyword = encodeURI(keyword);
  var myHeaders = new Headers();
  myHeaders.append(
    "sec-ch-ua",
    '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"'
  );
  myHeaders.append("x-li-lang", "en_US");
  myHeaders.append("sec-ch-ua-mobile", "?0");
  myHeaders.append(
    "User-Agent",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
  );
  myHeaders.append(
    "x-li-page-instance",
    "urn:li:page:d_flagship3_search_srp_content;9Jk/0mB9QayeSLyzbrTm7w=="
  );
  myHeaders.append("accept", "application/vnd.linkedin.normalized+json+2.1");
  myHeaders.append("csrf-token", JSessionID);
  myHeaders.append(
    "x-li-track",
    '{"clientVersion":"1.11.7073","mpVersion":"1.11.7073","osName":"web","timezoneOffset":1,"timezone":"Europe/Paris","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":2,"displayWidth":3360,"displayHeight":2100}'
  );
  myHeaders.append("x-restli-protocol-version", "2.0.0");
  myHeaders.append("sec-ch-ua-platform", '"macOS"');
  myHeaders.append("host", "www.linkedin.com");
  myHeaders.append(
    "cookie",
    `bcookie=\"v=2&485bf273-f1ea-408c-8436-0c7181d9156a\"; bscookie=\"v=1&20220331200952da5c1cf9-c60a-4f45-8fbe-997d305e6e6fAQEieB4BOi-aELplBFCgAKociJcd7tVo\"; li_alerts=e30=; G_ENABLED_IDPS=google; li_rm=AQE-_Q47sMVN1AAAAX_7SisP4fSnUvub_AMBS8DX3xN2Eu20FeASz36VFYhegsKW2tKxYRCBFXqZ2Rww1tinbptPLWlK6xYr23NbWEUmCH8EZKCWHO-K6CCa; _gcl_au=1.1.627853441.1649188418; JSESSIONID=\"${JSessionID}\"; li_theme=light; li_theme_set=app; liveagent_oref=https://www.linkedin.com/sales/search/people?companyIncluded=Viz.ai:17897131&companyTimeScope=CURRENT&keywords=; liveagent_ptid=0c11ec91-722f-4d91-ab8e-dcc53f092c3a; li_ep_auth_context=AE9hcHA9YWNjb3VudENlbnRlcixhaWQ9MTMxNzIxMjM0LGlpZD0tMSxwaWQ9MTYwNTY2NjUwLGV4cD0xNjUzNzkxNDA3MzM0LGN1cj10cnVlAceGcKxcGNw9ucMq8pSVQqZbImUJ; mp_52e5e0805583e8a410f1ed50d8e0c049_mixpanel={\"distinct_id\": \"181e3a93a177ba-008caacecca3cb-1c525635-1aeaa0-181e3a93a18a01\",\"$device_id\": \"181e3a93a177ba-008caacecca3cb-1c525635-1aeaa0-181e3a93a18a01\",\"$initial_referrer\": \"$direct\",\"$initial_referring_domain\": \"$direct\"}; timezone=Europe/Paris; aam_uuid=80685154479845086341700446948648622153; g_state={\"i_l\":0}; li_gc=MTsyMTsxNjY4MjU5ODcyOzI7MDIxWajV8j0mtSOrq2fBZ8KsqrnDmOm+vtdW+wXqaJFpC7w=; liveagent_vc=46; lms_ads=AQE9bVheN-SIeAAAAYWMNhZBFgJJ-hn0SX63IfB1FZ7J6wauuOlxHEOeE5iCW5-yOPbP4CEJpnGhbnsd1JyvqiRJgr-hWQky; lms_analytics=AQFIUxW1CodFbAAAAYWMNhZBya07N2o26lxNtcOmjru3xHE3k6pIrgdT62J_zw9iinDcxwrlOd7yCx7HgmEpF02ojOIuCosC; UserMatchHistory=AQIaXwaX-TkKsgAAAYW-_0ENo_TJc7H8E0ZqJ2uf9JzurABuk1YnyBHjZ9WTeQb5Sg9dbny0QeLsmw; AnalyticsSyncHistory=AQJKxTz251rDqgAAAYW-_0ENLC2ZT3buDdb67UW9KuZJ1XwWpN6bOuk-JWC1ewe_-VxXwKRGoz0LDh8FLhFf6w; li_at=${li_at}; liap=true; lang=v=2&lang=en-us; AMCVS_14215E3D5995C57C0A495C55@AdobeOrg=1; lidc=\"b=TB78:s=T:r=T:a=T:p=T:g=2988:u=736:x=1:i=1674322747:t=1674409147:v=2:sig=AQFnL4oTbeOUk4qzra4l0whKoYkmOXei\"; AMCV_14215E3D5995C57C0A495C55@AdobeOrg=-637568504|MCIDTS|19380|MCMID|80136092929184719531681562577197067138|MCAAMLH-1674995348|6|MCAAMB-1674995348|6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y|MCOPTOUT-1674397748s|NONE|vVersion|5.1.1|MCCIDH|1587226822; li_mc=MTsyMTsxNjc0MzkwOTM5OzI7MDIxIrh1LncJm9MKnXd3HqrPsAwTm3FK6e1G2PBp+9I6HOI=; _dd_s=logs=1&id=56e3a073-6c12-4089-90e6-3312d4853a2a&created=1674390541135&expire=1674392080122`
  );

  var requestOptions = {
    method: "GET",
    headers: myHeaders,
    redirect: "follow",
  };
  url_to_call_and_log = `https://www.linkedin.com/voyager/api/search/dash/clusters?decorationId=com.linkedin.voyager.dash.deco.search.SearchClusterCollection-175&origin=FACETED_SEARCH&q=all&query=(keywords:${encodedKeyword},flagshipSearchIntent:SEARCH_SRP,queryParameters:(datePosted:List(past-month),resultType:List(CONTENT)),includeFiltersInResponse:false)&start=${page}`;
  console.log(url_to_call_and_log);
  let response = await fetch(
    url_to_call_and_log,
    requestOptions
  );
  console.log(response.status);
  if (response.status == 200) {
    let json = await response.json();
    const elements = json["included"];
    let reactions = [];
    let posts = [];
    for (const e of elements) {
      if (e["numLikes"]) {
        reactions.push({
          postID: e["entityUrn"].split(
            "urn:li:fsd_socialActivityCounts:urn:li:activity:"
          )[1],
          likes: e["numLikes"],
          comments: e["numComments"],
        });
      } else {
        if (e["template"]) {
          posts.push({
            postID: e["trackingUrn"].split("urn:li:activity:")[1],
            author: e["title"]["text"],
            authorID: e["actorTrackingUrn"].split("urn:li:member:")[1],
            content: e["summary"]["text"],
            date_string: e["secondarySubtitle"]["text"],
          });
        }
      }
    }
    const results = posts.map((t1) => ({
      ...t1,
      ...reactions.find((t2) => t2.postID === t1.postID),
    }));
    //Save
    /* 
                var jsonContent = JSON.stringify({ "posts": results });
                fs.writeFile(`keyword_posts-p${page}.json`, jsonContent, 'utf8', function (err) {
                    if (err) {
                        console.log("An error occured while writing JSON Object to File.");
                        return console.log(err);
                    }
                    console.log("Keywords posts has been saved.");
                }); */

    return results;
  } else {
    console.log("Error GET Posts");
  }
}