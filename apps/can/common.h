#ifndef _COMMON_H
#define _COMMON_H

#include <assert.h>

#include <craton/syslog.h>

/* Linux kernel-style assertion macro */
#define BUG_ON(condition) assert(!(condition))
#define BUG() BUG_ON(1)

/* Default value of _TR_MODULE */
#if !defined _TR_MODULE
#define _TR_MODULE "?"
#endif

/* RTE period */
#define RTE_SCHEDULER_PERIOD_MS 40
#define RTE_CYCLES_PER_SECOND 25

/* Trace output formatting */
#define _TR_SYSLOG_FMT(fmt) "(%s) %s: " fmt "", _TR_MODULE, __func__

/* Helper for TR_DEBUG definition: if debug traces are disabled then wrap
   each debug trace statement so that it's compiled but then optimized away.
*/
#ifdef TR_DEBUG_ON
#define _TR_IF_DEBUG(...) __VA_ARGS__
#else
#define _TR_IF_DEBUG(...) while (0) { __VA_ARGS__; }
#endif

/* Trace macros */
#define TR_ERROR(fmt, ...) \
  syslog(LOG_ERR, _TR_SYSLOG_FMT(fmt), ## __VA_ARGS__)
#define TR_WARNING(fmt, ...) \
  syslog(LOG_WARNING, _TR_SYSLOG_FMT(fmt), ## __VA_ARGS__)
#define TR_NOTICE(fmt, ...) \
  syslog(LOG_NOTICE, _TR_SYSLOG_FMT(fmt), ## __VA_ARGS__)
#define TR_INFO(fmt, ...) \
  syslog(LOG_INFO, _TR_SYSLOG_FMT(fmt), ## __VA_ARGS__)
#define TR_DEBUG(fmt, ...) \
  _TR_IF_DEBUG(syslog(LOG_DEBUG, _TR_SYSLOG_FMT(fmt), ## __VA_ARGS__))

/* Avoids error 'ISO C99 requires rest arguments to be used' */
#define TR_ERROR_NO_ARGS(fmt) \
  syslog(LOG_ERR, _TR_SYSLOG_FMT(fmt))
#define TR_WARNING_NO_ARGS(fmt) \
  syslog(LOG_WARNING, _TR_SYSLOG_FMT(fmt))
#define TR_NOTICE_NO_ARGS(fmt) \
  syslog(LOG_NOTICE, _TR_SYSLOG_FMT(fmt))
#define TR_INFO_NO_ARGS(fmt) \
  syslog(LOG_INFO, _TR_SYSLOG_FMT(fmt))
#define TR_DEBUG_NO_ARGS(fmt) \
  _TR_IF_DEBUG(syslog(LOG_DEBUG,  _TR_SYSLOG_FMT(fmt)))

/* Macro that evaluates to `nbits' `1' bits */
#define BITMASK(nbits) ((1 << nbits) - 1)

/* Single `1' bit constants */
#define BIT31 (1 << 31)
#define BIT30 (1 << 30)
#define BIT29 (1 << 29)
#define BIT28 (1 << 28)
#define BIT27 (1 << 27)
#define BIT26 (1 << 26)
#define BIT25 (1 << 25)
#define BIT24 (1 << 24)
#define BIT23 (1 << 23)
#define BIT22 (1 << 22)
#define BIT21 (1 << 21)
#define BIT20 (1 << 20)
#define BIT19 (1 << 19)
#define BIT18 (1 << 18)
#define BIT17 (1 << 17)
#define BIT16 (1 << 16)
#define BIT15 (1 << 15)
#define BIT14 (1 << 14)
#define BIT13 (1 << 13)
#define BIT12 (1 << 12)
#define BIT11 (1 << 11)
#define BIT10 (1 << 10)
#define BIT9  (1 << 9)
#define BIT8  (1 << 8)
#define BIT7  (1 << 7)
#define BIT6  (1 << 6)
#define BIT5  (1 << 5)
#define BIT4  (1 << 4)
#define BIT3  (1 << 3)
#define BIT2  (1 << 2)
#define BIT1  (1 << 1)
#define BIT0  (1 << 0)

void print_set(int *set, char type);
void add_to_set(int *set, int element);

#endif /* _COMMON_H */
