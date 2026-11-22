<template>
  <!-- The answer's Markdown renderer parses in an async setup, which renders only under Suspense. -->
  <Suspense>
    <UApp>
      <RouterView />
    </UApp>
  </Suspense>
</template>
