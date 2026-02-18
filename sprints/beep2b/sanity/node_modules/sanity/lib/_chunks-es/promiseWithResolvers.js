const promiseWithResolvers = Promise.withResolvers?.bind(Promise) || function() {
  let resolve, reject;
  return {
    promise: new Promise((res, rej) => {
      resolve = res, reject = rej;
    }),
    resolve,
    reject
  };
};
export {
  promiseWithResolvers
};
//# sourceMappingURL=promiseWithResolvers.js.map
