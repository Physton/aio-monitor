# Soft UI Dashboard - `Dark Mode` Support

Soft UI Dashboard is built with over 70 frontend individual elements, like buttons, inputs, navbars, navtabs, cards or alerts, giving you the freedom of choosing and combining. All components can take variations in colour, that you can easily modify using SASS files and classes.

<br />

> **Enhanced version** of the [original version](https://www.creative-tim.com/product/soft-ui-dashboard?AFFILIATE=128200) with `Dark Mode` - [LIVE Demo](https://django-soft-ui-dashboard.appseed-srv1.com/)

- 👉 [Soft UI Dashboard](https://appseed.us/product/soft-ui-dashboard/django/) `Dark Support` - **Django Version** (free product)
- 👉 [Soft UI Dashboard](https://appseed.us/product/soft-ui-dashboard/flask/) `Dark Support` - **Flask Version** (free product)
- 🚀 [Soft Dashboard Generator](https://appseed.us/generator/soft-ui-dashboard/) - LIVE & Free Service

<br />

![Soft UI Dashboard - dark Mode Enhancement](https://user-images.githubusercontent.com/51070104/174716339-53c95c87-3842-4878-aef8-a675b0eca5b1.gif) 

<br />

## 👉 How it works

This enhancement was made by coding the following steps: 

- Create a new `JS` file that handles the user interactions
  - Source code: [dark-mode-handler.js](https://github.com/app-generator/sample-bootstrap5-dark-mode/blob/main/assets/js/dark-mode-handler.js)
- CSS/SCSS files for the style changes
  - Sources: [CSS](https://github.com/app-generator/sample-bootstrap5-dark-mode/blob/main/assets/css/dark-theme-core.css) and [SCSS](https://github.com/app-generator/sample-bootstrap5-dark-mode/blob/main/assets/scss/dark-theme-core.scss)
- Gulp scripts update to handle the new SCSS file

The new files (`dark-mode-handler.js` and `dark-theme-core.css`) are included in the pages. The CSS file goes to the `header` and the `JS` goes at the bottom, just before closing `</body>`.

On top of this, the `dark mode` is provided to be persistent and the current state of the theme (`dark` or `light`) is saved in the local storage on the browser. 

<br />

### 👉 JS Code

Once the `dark theme` control is saved in the navigation bar, and a simple event listener is attached that handles the user interaction.

```javascript
const themeSwitch = document.getElementById("theme-switch");
const themeIndicator = document.getElementById("theme-indicator");
const page = document.body;

const themeStates = ["light", "dark"]               // here we manage the states
const indicators = ["fa-moon", "fa-sun"]            // here is managed the icon 
const pageClass = ["bg-gray-100", "dark-page"]      // CSS class, where `bg-gray-100` was the original, light theme 

let currentTheme = localStorage.getItem("theme");   // Use the browser localStorage for persistence 

function setTheme(theme) {
    localStorage.setItem("theme", themeStates[theme])
}

function setIndicator(theme) {
    themeIndicator.classList.remove(indicators[0])
    themeIndicator.classList.remove(indicators[1])
    themeIndicator.classList.add(indicators[theme])
}

function setPage(theme) {
    page.classList.remove(pageClass[0])
    page.classList.remove(pageClass[1])
    page.classList.add(pageClass[theme])
}


if (currentTheme === null) {
    localStorage.setItem("theme", themeStates[0])
    setIndicator(0)
    setPage(0)
    themeSwitch.checked = true;
}
if (currentTheme === themeStates[0]) {
    setIndicator(0)
    setPage(0)
    themeSwitch.checked = true;

}
if (currentTheme === themeStates[1]) {
    setIndicator(1)
    setPage(1)
    themeSwitch.checked = false;
}


themeSwitch.addEventListener('change', function () {
    if (this.checked) {
        setTheme(0)
        setIndicator(0)
        setPage(0)
    } else {
        setTheme(1)
        setIndicator(1)
        setPage(1)
    }
});

```

<br />

### 👉 `Dark Mode` CSS File

Keep in in mind the rules of specificity [read more about it](https://developer.mozilla.org/en-US/docs/Web/CSS/Specificity) we start our SCSS file with the dark theme class selector for body tag. We will write all our code inside this code block. The css rules are pretty straightforward. 

The main thing to understand here is, when the dark mode is toggled, our body element gets a class of `dark-page` otherwise, it has the default class of “bg-gray-100”
In our main code block, we targetted our “dark-page” class and all elements are inside this body class, thus we can easily write new styles for this.

> Tips To Easily Change Dark Mode Colors

In the dark mode, we are not overwriting every bit of the page. The accent colors will remain the same. For example, buttons, alerts, badges, icons, etc.
The things we need to take care of includes, background for body, cards, card headers, list items, navigation buttons, input elements, svg icons, fontawesome icons, switches, and tables.

<br />

---
Soft UI Dashboard `Dark Mode` Support - Open-source sample provided by **[AppSeed](https://appseed.us/generator)**.  
