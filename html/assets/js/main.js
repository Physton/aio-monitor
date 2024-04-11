const {createApp} = Vue
createApp({
    data() {
        return {
            apiUrl: '',
            isShowLogin: false,
            loginData: {
                username: '',
                password: ''
            },
            accessToken: '',
            data: {},
            cardBackgroundColor: 'rgba(64, 75, 105, 0.8) !important',
            color_white: 'rgb(255,255,255)',
            color_green: 'rgb(35,199,123)',
            color_yellow: 'rgb(255,193,7)',
            color_purple: 'rgb(197,29,197)',
            color_blue: 'rgb(10,159,215)',
            color_red: 'rgb(255,75,75)',
            pve: [
                {title: '整机功耗', valueKey: 'pve_power', format: this.format_power},
                {title: 'CPU核心', valueKey: 'pve_cpu_count', defaultUnit: '核'},
                {title: 'CPU频率', valueKey: 'pve_cpu_freq', defaultUnit: 'MHz'},
                {title: 'CPU占用', valueKey: 'pve_cpu_usage', format: this.format_usage},
                {title: '内存总量', valueKey: 'pve_mem_total', format: this.format_size},
                {title: '内存占用', valueKey: 'pve_mem_usage', format: this.format_size},
                {title: 'CPU风扇', valueKey: 'pve_cpu_fan_value', defaultUnit: 'RPM'},
                {title: '硬盘风扇', valueKey: 'pve_disk_fan_value', defaultUnit: 'RPM'},
                {title: 'CPU温度', valueKey: 'pve_cpu_temp_value', format: this.format_temp},
                {title: 'M2温度', valueKey: 'pve_nvme_temp_value', format: this.format_temp},
            ],
            op: [
                {title: '系统运行时间', valueKey: 'op_uptime_str'},
                {title: 'CPU核心', valueKey: 'op_cpu_count', defaultUnit: '核'},
                {title: 'CPU频率', valueKey: 'op_cpu_freq', defaultUnit: 'MHz'},
                {title: 'CPU占用', valueKey: 'op_cpu_usage', format: this.format_usage},
                {title: 'CPU温度', valueKey: 'op_cpu_temp_value', format: this.format_temp},
                {title: '内存总量', valueKey: 'op_mem_total', format: this.format_size},
                {title: '内存占用', valueKey: 'op_mem_usage', format: this.format_size},
                {title: '客户端数', valueKey: 'op_client_num'},
                {title: '连接数', valueKey: 'op_connect_num'},
                {title: '总下载流量', valueKey: 'op_totaldown', format: this.format_size},
                {title: '总上传流量', valueKey: 'op_totalup', format: this.format_size},
                {title: '下载流量', valueKey: 'op_download', format: this.format_size_flow},
                {title: '上传流量', valueKey: 'op_upload', format: this.format_size_flow},
            ],
        }
    },
    mounted() {
        this.apiUrl = window.location.origin + '/api'
        this.accessToken = localStorage.getItem('access_token') || ''
        this.getData()
    },
    methods: {
        showLogin() {
            this.isShowLogin = true
        },
        successLogin(access_token) {
            this.accessToken = access_token
            this.isShowLogin = false
            localStorage.setItem('access_token', access_token)
        },
        onClickLogin() {
            if (!this.$refs.loginForm.reportValidity()) return
            console.log(this.loginData.username);
            console.log(this.loginData.password);
            axios.post(this.apiUrl + '/login', {
                username: this.loginData.username,
                password: SparkMD5.hash(SparkMD5.hash(this.loginData.password))
            }).then((response) => {
                this.successLogin(response.data.access_token)
            }).catch((error) => {
                alert('登陆失败，用户名或密码错误！')
            })
        },
        onClickFullScreen() {
            if (document.fullscreenElement) {
                document.exitFullscreen()
            } else {
                document.documentElement.requestFullscreen()
            }
        },
        getData() {
            if (this.isShowLogin) {
                setTimeout(this.getData, 1000)
                return
            }
            axios.get(this.apiUrl + '/data', {
                headers: {
                    'Authorization': 'Bearer ' + this.accessToken
                }
            }).then((response) => {
                let data = response.data.data
                document.body.style.backgroundImage = data.app_background_image ? 'url(' + data.app_background_image + ')' : 'none'
                document.body.style.backdropFilter = data.app_background_blur ? 'blur(' + data.app_background_blur + 'px)' : 'none'
                this.cardBackgroundColor = (data.app_card_background_color || 'rgba(64, 75, 105, 0.8)') + ' !important'
                if (data.addresses) {
                    data.addresses.forEach((address) => {
                        address.local_timeout_format = this.format_timeout(address, 'local_timeout')
                        address.public_timeout_format = this.format_timeout(address, 'public_timeout')
                        address.local_port_format = this.format_port(address, 'local_port_status')
                        address.public_port_format = this.format_port(address, 'public_port_status')
                    })
                }
                if (data.pve_qemus) {
                    data.pve_qemus.forEach((pve_qemu) => {
                        pve_qemu.cpu_format = this.format_usage(pve_qemu['cpu'])
                        pve_qemu.maxmem_format = this.format_size(pve_qemu['maxmem'])
                        pve_qemu.mem_format = this.format_size(pve_qemu['mem'])
                        pve_qemu.netin_format = this.format_size(pve_qemu['netin'])
                        pve_qemu.netout_format = this.format_size(pve_qemu['netout'])
                    })
                }
                if (data.dsm_storage) {
                    data.dsm_storage.data.disks.forEach((disk) => {
                        disk.size_total_format = this.format_size(disk['size_total'])
                        if (disk['diskType'] === 'SATA') {
                            disk.temp_format = this.format_hdd_temp(disk['temp'])
                        } else {
                            disk.temp_format = this.format_temp(disk['temp'])
                        }
                        if (disk['utilization']) {
                            disk.read_byte_format = this.format_size_flow(disk['utilization']['read_byte'])
                            disk.write_byte_format = this.format_size_flow(disk['utilization']['write_byte'])
                        } else {
                            disk.read_byte_format = {color: this.color_yellow, value: 'loading', unit: ''}
                            disk.write_byte_format = {color: this.color_yellow, value: 'loading', unit: ''}
                        }
                    })
                }

                const format = (item) => {
                    if (item.valueKey in data) {
                        item.value = data[item.valueKey]
                        if (item.value === 'N/A' || item.value === null || item.value === false || item.value === '') {
                            item.value = 'N/A'
                            item.unit = ''
                            item.color = this.color_yellow
                        } else {
                            item.unit = item.defaultUnit || ''
                            item.color = this.color_white
                            if (item.format) {
                                let res = item.format(item.value)
                                item.color = res.color
                                item.value = res.value
                                item.unit = res.unit
                            }
                        }
                    } else {
                        item.value = 'loading'
                        item.unit = ''
                        item.color = this.color_yellow
                    }
                }

                this.pve.forEach(format)
                this.op.forEach(format)

                this.data = data
            }).catch((error) => {
                console.log(error);
                if (error.response.status >= 400 && error.response.status < 500) {
                    this.showLogin()
                }
            }).finally(() => {
                setTimeout(this.getData, 1000)
            });
        },
        format_power(value) {
            let result = {color: '', value: '', unit: ''}
            result.unit = 'W'
            result.value = parseFloat(value)
            if (result.value <= 40) {
                result.color = this.color_green
            } else if (result.value <= 60) {
                result.color = this.color_yellow
            } else {
                result.color = this.color_red
            }
            return result
        },
        format_usage(value) {
            let result = {color: '', value: '', unit: ''}
            result.unit = '%'
            result.value = (parseFloat(value) * 100).toFixed(2)
            if (result.value <= 60) {
                result.color = this.color_green
            } else if (result.value <= 80) {
                result.color = this.color_yellow
            } else {
                result.color = this.color_red
            }
            return result
        },
        format_size(value) {
            let result = {color: '', value: '', unit: ''}
            result.value = parseFloat(value)
            if (result.value < 1024) {
                result.unit = 'B'
                result.color = this.color_green
            } else if (result.value < 1024 * 1024) {
                result.unit = 'KB'
                result.color = this.color_yellow
                result.value = result.value / 1024
            } else if (result.value < 1024 * 1024 * 1024) {
                result.unit = 'MB'
                result.color = this.color_purple
                result.value = result.value / 1024 / 1024
            } else if (result.value < 1024 * 1024 * 1024 * 1024) {
                result.unit = 'GB'
                result.color = this.color_blue
                result.value = result.value / 1024 / 1024 / 1024
            } else {
                result.unit = 'TB'
                result.color = this.color_red
                result.value = result.value / 1024 / 1024 / 1024 / 1024
            }
            result.value = result.value.toFixed(2)
            return result
        },
        format_size_flow(value) {
            let result = {color: '', value: '', unit: ''}
            result.value = parseFloat(value)
            if (result.value < 1024) {
                result.unit = 'B/s'
                result.color = this.color_green
            } else if (result.value < 1024 * 1024) {
                result.unit = 'KB/s'
                result.color = this.color_yellow
                result.value = result.value / 1024
            } else if (result.value < 1024 * 1024 * 1024) {
                result.unit = 'MB/s'
                result.color = this.color_purple
                result.value = result.value / 1024 / 1024
            } else if (result.value < 1024 * 1024 * 1024 * 1024) {
                result.unit = 'GB/s'
                result.color = this.color_blue
                result.value = result.value / 1024 / 1024 / 1024
            } else {
                result.unit = 'TB/s'
                result.color = this.color_red
                result.value = result.value / 1024 / 1024 / 1024 / 1024
            }
            result.value = result.value.toFixed(2)
            return result
        },
        format_temp(value) {
            let result = {color: '', value: '', unit: ''}
            result.value = parseFloat(value).toFixed(2)
            result.unit = '°C'
            if (result.value < 50) {
                result.color = this.color_green
            } else if (result.value < 70) {
                result.color = this.color_yellow
            } else {
                result.color = this.color_red
            }
            return result
        },
        format_hdd_temp(value) {
            let result = {color: '', value: '', unit: ''}
            result.value = parseFloat(value).toFixed(2)
            result.unit = '°C'
            if (result.value <= 35) {
                result.color = this.color_green
            } else if (result.value <= 45) {
                result.color = this.color_yellow
            } else {
                result.color = this.color_red
            }
            return result
        },
        format_timeout(address, key) {
            let result = {color: '', value: '', unit: ''}
            if (key in address) {
                if (address[key]) {
                    result.color = this.color_green
                    result.value = address[key]
                    result.unit = 'ms'
                } else {
                    result.color = this.color_red
                    result.value = 'timeout'
                    result.unit = ''
                }
            } else {
                result.color = this.color_yellow
                result.value = 'loading'
            }
            return result
        },
        format_port(address, key) {
            let result = {color: '', value: '', unit: ''}
            if (key in address) {
                if (address[key]) {
                    result.color = this.color_green
                    result.value = 'open'
                    result.unit = ''
                } else {
                    result.color = this.color_red
                    result.value = 'closed'
                    result.unit = ''
                }
            } else {
                result.color = this.color_yellow
                result.value = 'loading'
            }
            return result
        },
    }
}).mount('#app')