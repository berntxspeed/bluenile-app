//http://daynebatten.com/2015/07/raw-data-google-analytics/


(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', 'UA-77946306-2', 'auto');
// stuff up here goes into the general GA setup






// stuff down here goes into the extra 'custom' ga code dialog box
function getParameterByName(name, url) {
    if (!url) {
      url = window.location.href;
    }
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

// Private array of chars to use
  var CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'.split('');

  Math.uuid = function (len, radix) {
    var chars = CHARS, uuid = [], i;
    radix = radix || chars.length;

    if (len) {
      // Compact form
      for (i = 0; i < len; i++) uuid[i] = chars[0 | Math.random()*radix];
    } else {
      // rfc4122, version 4 form
      var r;

      // rfc4122 requires these characters
      uuid[8] = uuid[13] = uuid[18] = uuid[23] = '-';
      uuid[14] = '4';

      // Fill in random data.  At i==19 set the high bits of clock sequence as
      // per rfc4122, sec. 4.1.5
      for (i = 0; i < 36; i++) {
        if (!uuid[i]) {
          r = 0 | Math.random()*16;
          uuid[i] = chars[(i == 19) ? (r & 0x3) | 0x8 : r];
        }
      }
    }

    return uuid.join('');
  };


/* If the browser_id hasn't already been set... */
if (document.cookie.indexOf('browser_uuid_set=1') == -1) {

	/* Generate a UUID, and assign it to the browser_id custom dimension */
	ga('set', 'dimension1', Math.uuid());

	/* Set a cookie so we won't override the UUID we just set */
	document.cookie = 'browser_uuid_set=1; expires=Fri, 01 Jan 2100 12:00:00 UTC; domain=myshopify.com; path=/';
}

if (document.cookie.indexOf('emlhash_set=1') == -1) {

  /* grab emailhash from URL query string, if available */
  var emlhash = getParameterByName('emlhash');
  if(emlhash){
    console.log('emailhash='+emlhash);
    ga('set', 'dimension3', emlhash);
    ga('set', '&uid', emlhash);
    document.cookie = 'emlhash_set=1; expires=Fri, 01 Jan 2100 12:00:00 UTC; domain=myshopify.com; path=/';
  } else {
    console.log('didnt find emlhash in query string');
    /* if emailhash not in the URL query string - request it realtime
    by accessing it from shopify, then requesting it from bluenile app /emlhash-gen endpoint */
  }

}

/* Assign a timestamp to the utc_millisecs custom dimension */
ga('set', 'dimension2', new Date().getTime());

// Set the user ID using signed-in user_id
//<![CDATA[
//ga(‘set’, ‘&uid’, __st.cid);
//console.log('customerid='+customer_id);
//]]>

/* Send a pageview */
ga('send', 'pageview');
console.log('made it to end of GA code')