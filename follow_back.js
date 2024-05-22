(async () => {
  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const randomDelay = (min, max) => delay(Math.floor(Math.random() * (max - min + 1)) + min);
  let noActionDuration = 0;
  const maxNoActionDuration = 20000; // 20 seconds
  const start = Date.now();

  while (true) {
      const fadeInElements = document.querySelectorAll('.fade-in');
      let actionTaken = false;

      for (let fadeInElement of fadeInElements) {
          const buttons = fadeInElement.querySelectorAll('button');
          for (let button of buttons) {
              if (button.innerText === 'Follow' || button.getAttribute('aria-label')?.includes('Follow')) {
                  try {
                      button.click();
                      console.log('Clicked Follow');
                      actionTaken = true;
                      await randomDelay(500, 1000);
                  } catch (error) {
                      if (error.message.includes('429')) {
                          console.error('Error 429: Too Many Requests', error);
                          await delay(3000); // Wait 3 seconds on 429 error
                      } else {
                          console.error('Error: Error creating follow', error);
                      }
                  }
                  break;
              }
          }
          if (actionTaken) break;
      }

      if (!actionTaken) {
          window.scrollBy(0, 100);
          console.log('Scrolled down');
          await randomDelay(500, 1000);
          noActionDuration += 500;
      } else {
          noActionDuration = 0;
      }

      if (noActionDuration >= maxNoActionDuration) {
          console.log('No action for 20 seconds, stopping script');
          break;
      }

      if (Date.now() - start > 60000) { // Optional: Stop script after 60 seconds to prevent it from running indefinitely
          console.log('Script running too long, stopping script');
          break;
      }
  }
})();
