/*
 * Configure a list of redirects.
 */

import path from "path"

const redirects = {
  "/use/as/": "/needed/",
}

// Process the redirects by prefixing the site's base path if there is one.
export default function generateRedirects(basePath = "/") {
  Object.keys(redirects).forEach((key) => {
    redirects[key] = path.posix.join(basePath, redirects[key])
  })
  return redirects
}
