# -*- coding: utf-8 -*-

import os
import robot
import inspect

from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver.client_config import AppiumClientConfig
from AppiumLibrary.utils import ApplicationCache
from typing import Optional
from .keywordgroup import KeywordGroup


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class _ApplicationManagementKeywords(KeywordGroup):
    def __init__(self):
        self._cache = ApplicationCache()
        self._timeout_in_secs = float(5)

    # Public, open and close

    def close_application(self):
        """Closes the current application and also close webdriver session."""
        self._debug('Closing application with session id %s' % self._current_application().session_id)
        self._cache.close()

    def close_all_applications(self):
        """Closes all open applications.

        This keyword is meant to be used in test or suite teardown to
        make sure all the applications are closed before the test execution
        finishes.

        After this keyword, the application indices returned by `Open Application`
        are reset and start from `1`.
        """

        self._debug('Closing all applications')
        self._cache.close_all()

    def open_application(self, remote_url, alias=None, **kwargs):
        """Opens a new application to given Appium server.
        Capabilities of appium server, Android and iOS,
        Please check https://appium.io/docs/en/2.19/guides/caps/
        | *Option*            | *Man.* | *Description*     |
        | remote_url          | Yes    | Appium server url |
        | alias               | No     | alias             |

        Appium options can also be set using a dictionary (see example below with appium:options=&{APPIUM_OPTIONS}):
        | VAR    &{APPIUM_OPTIONS} |  deviceName=iPhone 15 Pro |  platformVersion=17.0 |  app=your.app |  automationName=XCUITest |

        Examples:
        | Open Application | http://localhost:4723 | alias=Myapp1         | platformName=iOS      | platformVersion=18.5            | deviceName=iPhone 16           | app=your.app                         |
        | Open Application | http://localhost:4723 | alias=Myapp1         | platformName=iOS      | platformVersion=18.5            | deviceName=iPhone 16           | app=your.app                         | ignore_certificates=False         |
        | Open Application | http://localhost:4723 | platformName=Android | platformVersion=4.2.2 | deviceName=192.168.56.101:5555 | app=${CURDIR}/demoapp/OrangeDemoApp.apk | appPackage=com.netease.qa.orangedemo | appActivity=MainActivity |
        | Open Application | http://localhost:4723 | platformName=iOS | appium:options=&{APPIUM_OPTIONS} |

        _*NOTE:*_ `Open Application` now uses the ClientConfig for configuration. If you encounter any issues or warnings when using this keyword, please refer to https://github.com/SeleniumHQ/selenium/blob/trunk/py/selenium/webdriver/remote/client_config.py
        """

        client_config = AppiumClientConfig(remote_url,
                                           direct_connection=kwargs.pop('direct_connection', True),
                                           keep_alive=kwargs.pop('keep_alive', False),
                                           ignore_certificates=kwargs.pop('ignore_certificates', True))

        options = AppiumOptions().load_capabilities(kwargs)
        application = webdriver.Remote(command_executor=remote_url, options=options, client_config=client_config)
        self._debug('Opened application with session id %s' % application.session_id)

        return self._cache.register(application, alias)

    def switch_application(self, index_or_alias):
        """Switches the active application by index or alias.

        `index_or_alias` is either application index (an integer) or alias
        (a string). Index is got as the return value of `Open Application`.

        This keyword returns the index of the previous active application,
        which can be used to switch back to that application later.

        Examples:
        | ${appium1}=              | Open Application  | http://localhost:4723/wd/hub                   | alias=MyApp1 | platformName=iOS | platformVersion=7.0 | deviceName='iPhone Simulator' | app=your.app |
        | ${appium2}=              | Open Application  | http://localhost:4755/wd/hub                   | alias=MyApp2 | platformName=iOS | platformVersion=7.0 | deviceName='iPhone Simulator' | app=your.app |
        | Click Element            | sendHello         | # Executed on appium running at localhost:4755 |
        | Switch Application       | ${appium1}        | # Switch using index                           |
        | Click Element            | ackHello          | # Executed on appium running at localhost:4723 |
        | Switch Application       | MyApp2            | # Switch using alias                           |
        | Page Should Contain Text | ackHello Received | # Executed on appium running at localhost:4755 |

        """
        old_index = self._cache.current_index
        if index_or_alias is None:
            self._cache.close()
        else:
            self._cache.switch(index_or_alias)
        return old_index

    def reset_application(self):
        """*DEPRECATED!!* in selenium v4, check `Terminate Application` keyword.

        Reset application. Open Application can be reset while Appium session is kept alive.
        """
        driver = self._current_application()
        driver.reset()

    def remove_application(self, application_id):
        """ Removes the application that is identified with an application id

        Example:
        | Remove Application |  com.netease.qa.orangedemo |

        """
        driver = self._current_application()
        driver.remove_app(application_id)

    def get_appium_timeout(self):
        """Gets the timeout in seconds that is used by various keywords.

        See `Set Appium Timeout` for an explanation."""
        return robot.utils.secs_to_timestr(self._timeout_in_secs)

    def set_appium_timeout(self, seconds):
        """Sets the timeout in seconds used by various keywords.

        There are several `Wait ...` keywords that take timeout as an
        argument. All of these timeout arguments are optional. The timeout
        used by all of them can be set globally using this keyword.

        The previous timeout value is returned by this keyword and can
        be used to set the old value back later. The default timeout
        is 5 seconds, but it can be altered in `importing`.

        Example:
        | ${orig timeout} = | Set Appium Timeout | 15 seconds |
        | Open page that loads slowly |
        | Set Appium Timeout | ${orig timeout} |
        """
        old_timeout = self.get_appium_timeout()
        self._timeout_in_secs = robot.utils.timestr_to_secs(seconds)
        return old_timeout

    def get_appium_sessionId(self):
        """Returns the current session ID as a reference"""
        self._info("Appium Session ID: " + self._current_application().session_id)
        return self._current_application().session_id

    def get_source(self):
        """Returns the entire source of the current page."""
        return self._current_application().page_source

    def log_source(self, loglevel='INFO'):
        """Logs and returns the entire html source of the current page or frame.

        The `loglevel` argument defines the used log level. Valid log levels are
        `WARN`, `INFO` (default), `DEBUG`, `TRACE` and `NONE` (no logging).
        """
        ll = loglevel.upper()
        if ll == 'NONE':
            return ''
        else:
            if  "run_keyword_and_ignore_error" not in [check_error_ignored[3] for check_error_ignored in inspect.stack()]:
                source = self._current_application().page_source
                self._log(source, ll)
                return source
            else:
                return ''

    def execute_script(self, script, **kwargs):
        """
        Execute a variety of native, mobile commands that aren't associated
        with a specific endpoint. See [https://appium.io/docs/en/commands/mobile-command/|Appium Mobile Command]
        for more details.

        Example:
        | &{scrollGesture}  |  create dictionary  |  left=${50}  |  top=${150}  |  width=${50}  |  height=${200}  |  direction=down  |  percent=${100}  |
        | Sleep             |  1                  |
        | Execute Script    |  mobile: scrollGesture  |  &{scrollGesture}  |

        """
        if kwargs:
            self._info(f"Provided dictionary: {kwargs}")

        return self._current_application().execute_script(script, kwargs)

    def execute_async_script(self, script, **kwargs):
        """
        Inject a snippet of Async-JavaScript into the page for execution in the
        context of the currently selected frame (Web context only).

        The executed script is assumed to be asynchronous and must signal that is done by
        invoking the provided callback, which is always provided as the final argument to the
        function.

        The value to this callback will be returned to the client.

        Check `Execute Script` for example kwargs usage

        """
        if kwargs:
            self._info(f"Provided dictionary: {kwargs}")

        return self._current_application().execute_async_script(script, kwargs)

    def execute_adb_shell(self, command, *args):
        """
        Execute ADB shell commands\n

        *Android only.*

        - _command_ - The ABD shell command
        - _args_ - Arguments to send to command

        Returns the exit code of ADB shell.

        Requires server flag --relaxed-security to be set on Appium server.
        """
        return self._current_application().execute_script('mobile: shell', {
            'command': command,
            'args': list(args)
        })

    def execute_adb_shell_timeout(self, command, timeout, *args):
        """
        Execute ADB shell commands\n

        *Android only.*

        - _command_ - The ABD shell command
        - _timeout_ - Timeout to be applied to command
        - _args_ - Arguments to send to command

        Returns the exit code of ADB shell.

        Requires server flag --relaxed-security to be set on Appium server.
        """
        return self._current_application().execute_script('mobile: shell', {
            'command': command,
            'args': list(args),
            'timeout': timeout
        })

    def go_back(self):
        """Goes one step backward in the browser history."""
        self._current_application().back()

    def lock(self, seconds=5):
        """
        Lock the device for a certain period of time.\n
        *iOS only.*
        """
        self._current_application().lock(robot.utils.timestr_to_secs(seconds))

    def background_application(self, seconds=5):
        """
        Puts the application in the background on the device for a certain
        duration.
        """
        self._current_application().background_app(seconds)


    def activate_application(self, app_id):
        """
        Activates the application if it is not running or is running in the background.
        Args:
         - app_id - BundleId for iOS. Package name for Android.

        """
        self._current_application().activate_app(app_id)

    def terminate_application(self, app_id):
        """
        Terminate the given app on the device

        Args:
         - app_id - BundleId for iOS. Package name for Android.

        """
        return self._current_application().terminate_app(app_id)

    def stop_application(self, app_id, timeout=5000, include_stderr=True):
        """
        Stop the given app on the device

        """
        self._current_application().execute_script('mobile: shell', {
            'command': 'am force-stop',
            'args': [app_id],
            'includeStderr': include_stderr,
            'timeout': timeout
        })

    def touch_id(self, match=True):
        """
        Simulate Touch ID on iOS Simulator

        `match` (boolean) whether the simulated fingerprint is valid (default true)

        """
        self._current_application().touch_id(match)

    def toggle_touch_id_enrollment(self):
        """
        Toggle Touch ID enrolled state on iOS Simulator

        """
        self._current_application().toggle_touch_id_enrollment()

    def shake(self):
        """
        Shake the device
        """
        self._current_application().shake()

    def portrait(self):
        """
        Set the device orientation to PORTRAIT
        """
        self._rotate('PORTRAIT')

    def landscape(self):
        """
        Set the device orientation to LANDSCAPE
        """
        self._rotate('LANDSCAPE')

    def get_current_context(self):
        """Get current context."""
        return self._current_application().current_context

    def get_contexts(self):
        """Get available contexts."""
        print(self._current_application().contexts)
        return self._current_application().contexts

    def get_window_height(self):
        """Get current device height.

        Example:
        | ${width}       | Get Window Width |
        | ${height}      | Get Window Height |
        | Click A Point  | ${width}         | ${height} |

        """
        return self._current_application().get_window_size()['height']

    def get_window_width(self):
        """Get current device width.

        Example:
        | ${width}       | Get Window Width |
        | ${height}      | Get Window Height |
        | Click A Point  | ${width}          | ${height} |

        """
        return self._current_application().get_window_size()['width']

    def switch_to_context(self, context_name):
        """Switch to a new context"""
        self._current_application().switch_to.context(context_name)

    def switch_to_frame(self, frame):
        """
        Switches focus to the specified frame, by index, name, or webelement.

        Example:
        | Go To Url | http://www.xxx.com |
        | Switch To Frame  | iframe_name |
        | Click Element | xpath=//*[@id="online-btn"] |
        """
        self._current_application().switch_to.frame(frame)

    def switch_to_parent_frame(self):
        """
        Switches focus to the parent context. If the current context is the top
        level browsing context, the context remains unchanged.
        """
        self._current_application().switch_to.parent_frame()

    def switch_to_window(self, window_name):
        """
        Switch to a new webview window if the application contains multiple webviews
        """
        self._current_application().switch_to.window(window_name)

    def go_to_url(self, url):
        """
        Opens URL in default web browser.

        Example:
        | Open Application  | http://localhost:4755/wd/hub | platformName=iOS | platformVersion=7.0 | deviceName='iPhone Simulator' | browserName=Safari |
        | Go To URL         | http://m.webapp.com          |
        """
        self._current_application().get(url)

    def get_capability(self, capability_name):
        """
        Return the desired capability value by desired capability name
        """
        try:
            capability = self._current_application().capabilities[capability_name]
        except Exception as e:
            raise e
        return capability

    def get_window_title(self):
        """Get the current Webview window title."""
        return self._current_application().title

    def get_window_url(self):
        """Get the current Webview window URL."""
        return self._current_application().current_url

    def get_windows(self):
        """Get available Webview windows."""
        print(self._current_application().window_handles)
        return self._current_application().window_handles

    def get_device_time(self, format: Optional[str] = None):
        """Returns the date and time from the device.

        Args:
            format:  The set of format specifiers. Read https://momentjs.com/docs/
                to get the full list of supported datetime format specifiers.
                If unset, default return format is `YYYY-MM-DDTHH:mm:ssZ`.

        Examples:
        ${device_time}    | Get Device Time | DD MM YYYY hh:mm:ss |
        ${device_time}    | Get Device Time | |

        Return:
            str: The date and time
        """
        return self._current_application().get_device_time(format)

    # Private

    def _current_application(self):
        if not self._cache.current:
            raise RuntimeError('No application is open')
        return self._cache.current

    def _get_platform(self):
        try:
            platform_name = self._current_application().capabilities['platformName']
        except Exception as e:
            raise e
        return platform_name.lower()

    def _is_platform(self, platform):
        platform_name = self._get_platform()
        return platform.lower() == platform_name

    def _is_ios(self):
        return self._is_platform('ios')

    def _is_android(self):
        return self._is_platform('android')

    def _rotate(self, orientation):
        driver = self._current_application()
        driver.orientation = orientation
